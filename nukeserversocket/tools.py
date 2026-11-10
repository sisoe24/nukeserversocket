"""Load the tools that clients may call, from a JSON tools file.

{
    "allow_arbitrary_code": false,
    "tools": [
        {
            "name": "publish_shot",
            "description": "Publish the open script as a new version of its shot.",
            "function": "studio_tools:publish_shot",
            "timeout": 600,
            "annotations": {"destructiveHint": false},
            "inputSchema": {"type": "object", "properties": {...}, "required": [...]}
        }
    ]
}

The tools file's folder is importable, so "function" can name a module next to it.
Without a tools file, code runs as before and there are no tools.

Clients use the tools with two requests; the reply is JSON:

    {"list_tools": true}
        -> {"allow_arbitrary_code": bool,
            "tools": [{"name", "description", "inputSchema", "timeout", "annotations"}],
            "skipped": {"name": "reason"}}
    {"call_tool": "publish_shot", "arguments": {"comment": "v2"}}
        -> {"ok": bool, "output": str, "images": [{"mimeType": str, "data": base64 str}]}

"images" is there only when the tool returns an Image.
"""
from __future__ import annotations

import os
import re
import sys
import json
import base64
import shutil
import inspect
import pathlib
import importlib
import traceback
from typing import Any, Dict, Tuple, Callable, Optional
from dataclasses import field, dataclass

from .utils import stdoutIO
from .logger import get_logger

LOGGER = get_logger()

BUILTIN_TOOL = 'nuke_execute_code'

_NAME = re.compile(r'^[A-Za-z0-9_.-]{1,128}$')

# MCP tool annotations: hints clients use, for example to skip approval for read-only tools
_HINTS = ('readOnlyHint', 'destructiveHint', 'idempotentHint', 'openWorldHint')


@dataclass
class Tool:
    name: str
    description: str
    input_schema: Dict[str, Any]
    function: Callable[..., Any]
    timeout: Optional[float] = None
    annotations: Optional[Dict[str, Any]] = None


@dataclass
class Image:
    """Return this from a tool to send an image to the client."""
    data: bytes
    mime_type: str = 'image/jpeg'


class ToolError(Exception):
    """Raise from a tool to fail with this message only, without a traceback."""


@dataclass
class ToolSet:
    allow_arbitrary_code: bool = True
    tools: Dict[str, Tool] = field(default_factory=dict)
    # the panel's own tools, e.g. nuke_vision; independent of allow_arbitrary_code
    builtins: Dict[str, Tool] = field(default_factory=dict)
    # tool name (or entry position) -> why it was not loaded
    skipped: Dict[str, str] = field(default_factory=dict)
    # why code is off, naming the file, for logs and client errors
    code_off_reason: str = field(default='', compare=False)


# repo root, next to the package: copy installs and the release zip ship it, pip does not
SAMPLE_DIR = pathlib.Path(__file__).parents[1] / 'resources' / 'sample'


def create_sample(folder: str) -> str:
    """Copy the sample tools file and its module into `folder`; return the tools file path."""
    target = pathlib.Path(folder)
    files = [p for p in SAMPLE_DIR.iterdir() if p.is_file()]
    existing = [p.name for p in files if (target / p.name).exists()]
    if existing:
        raise FileExistsError(f'{", ".join(existing)} already in {target}.')
    for source in files:
        shutil.copyfile(source, target / source.name)
    return str(target / 'nss_tools.json')


def _import_function(reference: str) -> Callable[..., Any]:
    module_name, _, attr_path = reference.partition(':')
    if not module_name or not attr_path:
        raise ValueError(f'"function" must look like "module:function", got {reference!r}.')

    obj: Any = importlib.import_module(module_name)
    for attr in attr_path.split('.'):
        obj = getattr(obj, attr)

    if not callable(obj):
        raise TypeError(f'{reference} is not callable.')
    return obj


def _check_annotations(annotations: Any) -> None:
    if not isinstance(annotations, dict):
        raise ValueError('"annotations" must be an object.')
    for key, value in annotations.items():
        if key == 'title':
            if not isinstance(value, str):
                raise ValueError('"annotations.title" must be a string.')
        elif key in _HINTS:
            if not isinstance(value, bool):
                raise ValueError(f'"annotations.{key}" must be true or false.')
        else:
            raise ValueError(f'unknown annotation {key!r}; use title or {", ".join(_HINTS)}.')


def _check_schema(schema: Any) -> None:
    if not isinstance(schema, dict) or schema.get('type') != 'object':
        raise ValueError('"inputSchema" must be an object schema: {"type": "object", ...}.')

    properties = schema.get('properties', {})
    required = schema.get('required', [])
    if not isinstance(properties, dict):
        raise ValueError('"inputSchema.properties" must be an object.')
    if not all(isinstance(spec, dict) for spec in properties.values()):
        raise ValueError('each property in "inputSchema.properties" must be an object.')
    if not isinstance(required, list) or not all(isinstance(key, str) for key in required):
        raise ValueError('"inputSchema.required" must be a list of names.')

    unknown = [key for key in required if key not in properties]
    if unknown:
        raise ValueError(f'"required" names properties that do not exist: {unknown}.')


def _check_signature(function: Callable[..., Any], schema: Dict[str, Any]) -> None:
    """Fail at load time on what would otherwise be a TypeError at call time."""
    try:
        params = inspect.signature(function).parameters.values()
    except (TypeError, ValueError) as e:
        raise ValueError(f'cannot read the function signature ({e}).') from e

    if any(p.kind is p.POSITIONAL_ONLY and p.default is p.empty for p in params):
        raise ValueError('positional-only parameters cannot be passed by name.')

    properties = schema.get('properties', {})
    required = set(schema.get('required', []))
    named = {p.name: p for p in params if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)}

    if not any(p.kind is p.VAR_KEYWORD for p in params):
        extra = [key for key in properties if key not in named]
        if extra:
            raise ValueError(f'schema properties missing from the function signature: {extra}.')

    missing = [name for name, p in named.items() if p.default is p.empty and name not in required]
    if missing:
        raise ValueError(f'function parameters without a default must be "required": {missing}.')


def _load_tool(entry: Any, loaded: Dict[str, Tool]) -> Tool:
    if not isinstance(entry, dict):
        raise ValueError('entry must be an object.')

    name = entry.get('name')
    if not isinstance(name, str) or not _NAME.match(name):
        raise ValueError('"name" must be 1-128 characters of letters, digits, "_", "-" or ".".')
    if name == BUILTIN_TOOL:
        raise ValueError(f'"{BUILTIN_TOOL}" is reserved for the built-in tool.')
    if name in loaded:
        raise ValueError('a tool with this name is already loaded.')

    description = entry.get('description')
    if not isinstance(description, str) or not description.strip():
        raise ValueError('"description" must be a non-empty string.')

    timeout = entry.get('timeout')
    if timeout is not None and (isinstance(timeout, bool) or
                                not isinstance(timeout, (int, float)) or timeout <= 0):
        raise ValueError('"timeout" must be a positive number of seconds.')

    schema = entry.get('inputSchema', {'type': 'object', 'properties': {}})
    _check_schema(schema)

    annotations = entry.get('annotations')
    if annotations is not None:
        _check_annotations(annotations)

    reference = entry.get('function')
    if not isinstance(reference, str):
        raise ValueError('"function" must be a string like "module:function".')

    try:
        function = _import_function(reference)
    except Exception as e:
        # studio code can raise anything at import; one broken module must not stop the rest
        raise ValueError(f'cannot load {reference!r}: {type(e).__name__}: {e}') from e

    _check_signature(function, schema)
    return Tool(name, description, schema, function, timeout, annotations)


def load_tools(path: Optional[str] = None, builtins: Optional[Dict[str, Tool]] = None) -> ToolSet:
    """Load the tool file at `path`, or at NSS_TOOLS when `path` is None.

    `builtins` are listed whatever the file says. A tool file that is set but
    cannot be read turns code execution off: falling back to the default would
    reopen arbitrary code on a locked-down install.
    """
    builtins = dict(builtins or {})
    path = os.environ.get('NSS_TOOLS') if path is None else path
    if not path:
        return ToolSet(builtins=builtins)
    name = pathlib.Path(path).name

    try:
        config = json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        LOGGER.error('Cannot read the tools file %s (%s). Code execution is off.', path, e)
        return ToolSet(allow_arbitrary_code=False, builtins=builtins,
                       code_off_reason=f'cannot read {name}')

    if not isinstance(config, dict):
        LOGGER.error('The tools file %s must hold a JSON object. Code execution is off.', path)
        return ToolSet(allow_arbitrary_code=False, builtins=builtins,
                       code_off_reason=f'{name} is not a JSON object')

    allow_arbitrary_code = config.get('allow_arbitrary_code', True)
    reason = f'allow_arbitrary_code is false in {name}'
    if not isinstance(allow_arbitrary_code, bool):
        LOGGER.error('"allow_arbitrary_code" in %s must be true or false. '
                     'Code execution is off.', path)
        allow_arbitrary_code, reason = False, f'allow_arbitrary_code is not true or false in {name}'

    entries = config.get('tools', [])
    if not isinstance(entries, list):
        LOGGER.error('"tools" in %s must be a list. No tools loaded.', path)
        entries = []

    # lets "function" name a module next to the tools file, with no NUKE_PATH setup
    folder = str(pathlib.Path(path).resolve().parent)
    if folder not in sys.path:
        sys.path.append(folder)

    toolset = ToolSet(allow_arbitrary_code=allow_arbitrary_code, builtins=builtins,
                      code_off_reason='' if allow_arbitrary_code else reason)
    for index, entry in enumerate(entries):
        label = entry.get('name') if isinstance(entry, dict) else None
        label = label if isinstance(label, str) and label else f'tools[{index}]'
        try:
            tool = _load_tool(entry, {**toolset.builtins, **toolset.tools})
        except ValueError as e:
            LOGGER.warning('Skipped tool %s: %s', label, e)
            toolset.skipped[label] = str(e)
            continue
        toolset.tools[tool.name] = tool

    # the panel logs the summary when it starts listening
    LOGGER.debug(
        'Loaded %s tool(s) from %s, %s skipped. Code execution is %s.',
        len(toolset.tools), path, len(toolset.skipped), 'on' if allow_arbitrary_code else 'off',
    )
    return toolset


_JSON_TYPES: Dict[str, Callable[[Any], bool]] = {
    'string': lambda v: isinstance(v, str),
    'integer': lambda v: isinstance(v, int) and not isinstance(v, bool),
    'number': lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    'boolean': lambda v: isinstance(v, bool),
    'array': lambda v: isinstance(v, list),
    'object': lambda v: isinstance(v, dict),
    'null': lambda v: v is None,
}


def _check_arguments(tool: Tool, arguments: Dict[str, Any]) -> None:
    """Check names, `type` and `enum` only: stdlib has no JSON Schema validator."""
    properties = tool.input_schema.get('properties', {})

    missing = [key for key in tool.input_schema.get('required', []) if key not in arguments]
    if missing:
        raise ValueError(f'missing required argument(s): {missing}.')

    takes_kwargs = any(
        p.kind is p.VAR_KEYWORD for p in inspect.signature(tool.function).parameters.values()
    )
    for key, value in arguments.items():
        if key not in properties:
            if takes_kwargs:
                continue
            raise ValueError(f'unknown argument {key!r}. Expected: {sorted(properties)}.')

        spec = properties[key]
        types = spec.get('type')
        types = [types] if isinstance(types, str) else types or []
        if types and not any(_JSON_TYPES.get(t, lambda v: True)(value) for t in types):
            raise ValueError(f'{key!r} must be {" or ".join(types)}, got {value!r}.')
        if 'enum' in spec and value not in spec['enum']:
            raise ValueError(f'{key!r} must be one of {spec["enum"]}, got {value!r}.')


def _format_result(result: Any) -> str:
    if result is None:
        return ''
    if isinstance(result, str):
        return result
    return json.dumps(result, default=str)


def call_tool(toolset: ToolSet, name: str, arguments: Any = None) -> Dict[str, Any]:
    """Call a loaded tool and return {"ok": bool, "output": str}.

    The output is what the tool printed, followed by its return value. An Image
    return value goes to "images" instead. A failure returns ok False with the
    reason, so the caller never has to read the text: a ToolError gives its
    message, any other exception its traceback.
    """
    tool = toolset.builtins.get(name) or toolset.tools.get(name)
    if tool is None:
        reason = toolset.skipped.get(name)
        if reason:
            return {'ok': False, 'output': f'Tool {name!r} was not loaded: {reason}'}
        available = sorted({**toolset.builtins, **toolset.tools})
        return {'ok': False, 'output': f'Unknown tool {name!r}. Available: {available}.'}

    arguments = {} if arguments is None else arguments
    if not isinstance(arguments, dict):
        return {'ok': False, 'output': 'Arguments must be a JSON object.'}

    try:
        _check_arguments(tool, arguments)
    except ValueError as e:
        return {'ok': False, 'output': f'Invalid arguments: {e}'}

    with stdoutIO() as printed:
        try:
            result = tool.function(**arguments)
        except ToolError as e:
            return {'ok': False, 'output': printed.getvalue() + str(e)}
        except Exception:
            return {'ok': False, 'output': printed.getvalue() + traceback.format_exc()}

    if isinstance(result, Image):
        image = {'mimeType': result.mime_type, 'data': base64.b64encode(result.data).decode('ascii')}
        return {'ok': True, 'output': printed.getvalue(), 'images': [image]}
    return {'ok': True, 'output': printed.getvalue() + _format_result(result)}


def list_tools(toolset: ToolSet) -> Dict[str, Any]:
    return {
        'allow_arbitrary_code': toolset.allow_arbitrary_code,
        'tools': [
            {'name': t.name, 'description': t.description,
             'inputSchema': t.input_schema, 'timeout': t.timeout,
             'annotations': t.annotations}
            for t in [*toolset.builtins.values(), *toolset.tools.values()]
        ],
        'skipped': toolset.skipped,
    }


def parse_tool_request(raw: bytes) -> Optional[Dict[str, Any]]:
    """Return the request when it is a tool request, else None for the code path."""
    try:
        request = json.loads(raw)
    except ValueError:
        return None
    if isinstance(request, dict) and ('list_tools' in request or 'call_tool' in request):
        return request
    return None


def _last_line(output: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    return lines[-1][:200] if lines else 'no output'


def handle_tool_request(toolset: ToolSet, request: Dict[str, Any]) -> Tuple[str, bool, str]:
    """Return the JSON reply, whether the request succeeded, and what to log about it."""
    if 'call_tool' not in request:
        reply = list_tools(toolset)
        return json.dumps(reply, default=str), True, f'list tools: {len(reply["tools"])}'

    name = request['call_tool']
    if isinstance(name, str):
        try:
            reply = call_tool(toolset, name, request.get('arguments'))
        except Exception:
            # e.g. a schema the argument check cannot read; the client must get a reply
            reply = {'ok': False, 'output': traceback.format_exc()}
    else:
        name = repr(name)
        reply = {'ok': False, 'output': '"call_tool" must be a tool name.'}

    summary = f'{name}: ok' if reply['ok'] else f'{name}: {_last_line(reply["output"])}'
    return json.dumps(reply, default=str), reply['ok'], summary
