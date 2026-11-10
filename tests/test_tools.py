from __future__ import annotations

import sys
import json
import types
import textwrap

import pytest

from nukeserversocket.tools import (BUILTIN_TOOL, SAMPLE_DIR, Tool, Image, ToolSet, ToolError,
                                    call_tool, list_tools, load_tools, create_sample,
                                    handle_tool_request)

MODULE = 'nss_test_studio_tools'

MODULE_SOURCE = '''
def publish_shot(comment, version=None):
    return 'published'

def chatty(shot):
    print('looking up', shot)
    return {'shot': shot, 'frames': [1001, 1100]}

def fails(shot):
    print('started')
    raise RuntimeError('no write node')

def typed(name, count=1, scale=1.0, flag=False, tags=None, mode='fast', note=None):
    return 'ok'

def no_args():
    return 'ok'

def with_kwargs(shot, **options):
    return shot

def positional_only(shot, /):
    return shot

NOT_CALLABLE = 42
'''


@pytest.fixture(autouse=True)
def restore_sys_path(monkeypatch):
    """load_tools adds the tool file's folder to sys.path."""
    monkeypatch.setattr(sys, 'path', list(sys.path))


@pytest.fixture()
def studio_module(tmp_path, monkeypatch):
    """A studio module on sys.path, so "function" references can import it."""
    (tmp_path / f'{MODULE}.py').write_text(textwrap.dedent(MODULE_SOURCE))
    (tmp_path / 'nss_test_broken.py').write_text('raise RuntimeError("boom at import")\n')
    monkeypatch.syspath_prepend(str(tmp_path))
    yield
    sys.modules.pop(MODULE, None)
    sys.modules.pop('nss_test_broken', None)


@pytest.fixture()
def tool_file(tmp_path, studio_module):
    """Write a tool file and return its path."""
    def write(config) -> str:
        path = tmp_path / 'nss_tools.json'
        path.write_text(config if isinstance(config, str) else json.dumps(config))
        return str(path)
    return write


def _tool(**overrides) -> dict:
    tool = {
        'name': 'publish_shot',
        'description': 'Publish the open script.',
        'function': f'{MODULE}:publish_shot',
        'inputSchema': {
            'type': 'object',
            'properties': {'comment': {'type': 'string'}, 'version': {'type': 'integer'}},
            'required': ['comment'],
        },
    }
    tool.update(overrides)
    return tool


def test_no_tool_file_keeps_todays_behaviour(monkeypatch):
    """Without NSS_TOOLS, code runs as before and no tools are loaded."""
    monkeypatch.delenv('NSS_TOOLS', raising=False)
    assert load_tools() == ToolSet(allow_arbitrary_code=True)


def test_tool_file_is_read_from_env(tool_file, monkeypatch):
    """NSS_TOOLS names the tool file."""
    monkeypatch.setenv('NSS_TOOLS', tool_file({'allow_arbitrary_code': False, 'tools': [_tool()]}))
    toolset = load_tools()
    assert toolset.allow_arbitrary_code is False
    assert list(toolset.tools) == ['publish_shot']


@pytest.mark.parametrize('content', ['{not json', '[]', '"text"'])
def test_unreadable_tool_file_turns_code_off(tool_file, content):
    """A tool file that is set but broken must not fall back to allowing code."""
    toolset = load_tools(tool_file(content))
    assert toolset == ToolSet(allow_arbitrary_code=False)


def test_missing_tool_file_turns_code_off(tmp_path):
    """A tool file that is set but missing must not fall back to allowing code."""
    assert load_tools(str(tmp_path / 'missing.json')) == ToolSet(allow_arbitrary_code=False)


@pytest.mark.parametrize('value', ['false', 0, None])
def test_non_boolean_allow_arbitrary_code_turns_code_off(tool_file, value):
    """Only a real JSON true allows code; anything else is treated as off."""
    assert load_tools(tool_file({'allow_arbitrary_code': value})).allow_arbitrary_code is False


def test_allow_arbitrary_code_defaults_to_true_in_a_tool_file(tool_file):
    """A tool file that only adds tools keeps code execution on."""
    assert load_tools(tool_file({'tools': [_tool()]})).allow_arbitrary_code is True


def test_valid_tool_is_loaded(tool_file):
    """A valid entry loads with its function, schema and timeout."""
    toolset = load_tools(tool_file({'tools': [_tool(timeout=600)]}))
    tool = toolset.tools['publish_shot']
    assert tool.function(comment='x') == 'published'
    assert tool.timeout == 600
    assert tool.input_schema['required'] == ['comment']
    assert toolset.skipped == {}


def test_omitted_schema_is_allowed_for_functions_without_arguments(tool_file):
    """A tool with no arguments needs no inputSchema."""
    entry = _tool(name='ping', function=f'{MODULE}:no_args')
    del entry['inputSchema']
    toolset = load_tools(tool_file({'tools': [entry]}))
    assert toolset.tools['ping'].input_schema == {'type': 'object', 'properties': {}}


def test_kwargs_function_accepts_extra_properties(tool_file):
    """With **kwargs, schema properties do not have to be named parameters."""
    entry = _tool(name='render', function=f'{MODULE}:with_kwargs', inputSchema={
        'type': 'object',
        'properties': {'shot': {'type': 'string'}, 'quality': {'type': 'string'}},
        'required': ['shot'],
    })
    assert 'render' in load_tools(tool_file({'tools': [entry]})).tools


@pytest.mark.parametrize('overrides, reason', [
    ({'function': 'nss_test_missing_module:publish_shot'}, 'ModuleNotFoundError'),
    ({'function': 'nss_test_broken:anything'}, 'boom at import'),
    ({'function': f'{MODULE}:missing'}, 'AttributeError'),
    ({'function': f'{MODULE}:NOT_CALLABLE'}, 'not callable'),
    ({'function': 'no_colon'}, 'module:function'),
    ({'function': 42}, 'module:function'),
    ({'name': 'bad name'}, '"name"'),
    ({'name': BUILTIN_TOOL}, 'reserved'),
    ({'description': ' '}, '"description"'),
    ({'timeout': 0}, '"timeout"'),
    ({'timeout': True}, '"timeout"'),
    ({'annotations': []}, '"annotations" must be an object'),
    ({'annotations': {'readOnlyHint': 'yes'}}, 'must be true or false'),
    ({'annotations': {'title': 1}}, '"annotations.title"'),
    ({'annotations': {'readonly': True}}, "unknown annotation 'readonly'"),
    ({'inputSchema': {'type': 'array'}}, 'object schema'),
    ({'inputSchema': {'type': 'object', 'properties': [], 'required': []}}, 'properties'),
    ({'inputSchema': {'type': 'object', 'properties': {}, 'required': ['ghost']}}, 'do not exist'),
    ({'inputSchema': {'type': 'object', 'properties': {'comment': True}}}, 'each property'),
    ({'inputSchema': {'type': 'object', 'properties': {'comment': {}, 'shot': {}},
                      'required': ['comment']}}, 'missing from the function signature'),
    ({'inputSchema': {'type': 'object', 'properties': {'comment': {}}}}, 'must be "required"'),
    ({'function': f'{MODULE}:positional_only',
      'inputSchema': {'type': 'object', 'properties': {'shot': {}}, 'required': ['shot']}},
     'positional-only'),
])
def test_bad_entry_is_skipped_with_reason(tool_file, overrides, reason):
    """A bad entry is skipped with a readable reason, and the next entry still loads."""
    good = _tool(name='still_loads')
    toolset = load_tools(tool_file({'tools': [_tool(**overrides), good]}))

    assert list(toolset.tools) == ['still_loads']
    assert len(toolset.skipped) == 1
    assert reason in next(iter(toolset.skipped.values()))


def test_duplicate_name_skips_the_second_entry(tool_file):
    """The first entry with a name wins; the duplicate is reported."""
    toolset = load_tools(tool_file({'tools': [_tool(), _tool(description='Second.')]}))
    assert toolset.tools['publish_shot'].description == 'Publish the open script.'
    assert 'already loaded' in toolset.skipped['publish_shot']


def test_non_object_entries_are_skipped_by_position(tool_file):
    """Entries that are not objects are reported by their position."""
    toolset = load_tools(tool_file({'tools': ['oops', _tool()]}))
    assert 'tools[0]' in toolset.skipped
    assert 'publish_shot' in toolset.tools


def test_non_list_tools_loads_nothing_but_keeps_policy(tool_file):
    """A malformed "tools" value loads nothing and still applies allow_arbitrary_code."""
    toolset = load_tools(tool_file({'allow_arbitrary_code': False, 'tools': {'publish_shot': {}}}))
    assert toolset == ToolSet(allow_arbitrary_code=False)


@pytest.mark.parametrize('content, reason', [
    ('{not json', 'cannot read nss_tools.json'),
    ('[]', 'nss_tools.json is not a JSON object'),
    ('{"allow_arbitrary_code": 0}', 'allow_arbitrary_code is not true or false in nss_tools.json'),
    ('{"allow_arbitrary_code": false}', 'allow_arbitrary_code is false in nss_tools.json'),
    ('{}', ''),
])
def test_code_off_reason_names_the_cause(tool_file, content, reason):
    assert load_tools(tool_file(content)).code_off_reason == reason


def test_module_next_to_the_tool_file_imports(tmp_path, monkeypatch):
    """The tool file's folder is importable, so adapters need no NUKE_PATH entry."""
    (tmp_path / 'nss_test_adapter.py').write_text('def ping():\n    return "pong"\n')
    path = tmp_path / 'nss_tools.json'
    path.write_text(json.dumps({'tools': [
        {'name': 'ping', 'description': 'Ping.', 'function': 'nss_test_adapter:ping'}]}))

    toolset = load_tools(str(path))
    sys.modules.pop('nss_test_adapter', None)

    assert toolset.tools['ping'].function() == 'pong'


def test_sample_tool_file_loads_every_tool(monkeypatch):
    """The sample that Create sample copies stays valid."""
    monkeypatch.setitem(sys.modules, 'nuke', types.ModuleType('nuke'))
    toolset = load_tools(str(SAMPLE_DIR / 'nss_tools.json'))
    sys.modules.pop('nss_tools_example', None)

    assert toolset.allow_arbitrary_code is True
    assert list(toolset.tools) == ['script_info', 'list_writes', 'render_write']
    assert toolset.skipped == {}


def test_create_sample_copies_the_sample(tmp_path):
    path = create_sample(str(tmp_path))
    assert path == str(tmp_path / 'nss_tools.json')
    assert sorted(p.name for p in tmp_path.iterdir()) == ['nss_tools.json', 'nss_tools_example.py']


def test_create_sample_keeps_existing_files(tmp_path):
    (tmp_path / 'nss_tools.json').write_text('mine')
    with pytest.raises(FileExistsError, match='nss_tools.json'):
        create_sample(str(tmp_path))
    assert (tmp_path / 'nss_tools.json').read_text() == 'mine'
    assert not (tmp_path / 'nss_tools_example.py').exists()


@pytest.fixture()
def toolset(tool_file):
    """A toolset with tools covering output, failures and argument types."""
    def entry(name, properties, required):
        return {'name': name, 'description': f'{name} tool.', 'function': f'{MODULE}:{name}',
                'inputSchema': {'type': 'object', 'properties': properties, 'required': required}}

    return load_tools(tool_file({'tools': [
        entry('chatty', {'shot': {'type': 'string'}}, ['shot']),
        entry('fails', {'shot': {'type': 'string'}}, ['shot']),
        entry('typed', {
            'name': {'type': 'string'},
            'count': {'type': 'integer'},
            'scale': {'type': 'number'},
            'flag': {'type': 'boolean'},
            'tags': {'type': 'array'},
            'mode': {'type': 'string', 'enum': ['fast', 'best']},
            'note': {'type': ['string', 'null']},
        }, ['name']),
        entry('with_kwargs', {'shot': {'type': 'string'}}, ['shot']),
        {'name': 'broken', 'description': 'Broken.', 'function': 'nss_test_broken:x'},
    ]}))


def test_call_returns_printed_output_then_result(toolset):
    """Printed output comes first, then the return value as JSON."""
    assert call_tool(toolset, 'chatty', {'shot': 'sh010'}) == {
        'ok': True, 'output': 'looking up sh010\n{"shot": "sh010", "frames": [1001, 1100]}'}


def test_call_failure_reports_printed_output_and_traceback(toolset):
    """An exception gives ok False with what was printed and the traceback."""
    result = call_tool(toolset, 'fails', {'shot': 'sh010'})
    assert result['ok'] is False
    assert result['output'].startswith('started\nTraceback (most recent call last):')
    assert 'RuntimeError: no write node' in result['output']


def test_unexpected_error_still_gets_a_reply():
    """A failure outside the tool, here an unreadable type, replies ok False instead of raising."""
    schema = {'type': 'object', 'properties': {'node': {'type': [{}]}}}
    toolset = ToolSet(builtins={'odd': Tool('odd', 'Odd schema.', schema, lambda node: node)})
    output, ok, _ = handle_tool_request(toolset, {'call_tool': 'odd', 'arguments': {'node': 'x'}})
    assert ok is False and 'TypeError' in json.loads(output)['output']


def test_tool_error_reports_only_its_message():
    """A ToolError gives ok False with what was printed and the message, no traceback."""
    def refuse():
        print('looking')
        raise ToolError('No node named Read9.')

    toolset = ToolSet(builtins={'refuse': Tool('refuse', 'Refuses.', {'type': 'object'}, refuse)})
    assert call_tool(toolset, 'refuse') == {'ok': False, 'output': 'looking\nNo node named Read9.'}


def test_call_restores_stdout_after_failure(toolset):
    """Output capture is undone even when the tool raises."""
    stdout = sys.stdout
    call_tool(toolset, 'fails', {'shot': 'sh010'})
    assert sys.stdout is stdout


@pytest.mark.parametrize('arguments', [
    {'name': 'x'},
    {'name': 'x', 'count': 2, 'scale': 2, 'flag': True, 'tags': [], 'mode': 'best', 'note': None},
    {'name': 'x', 'scale': 0.5, 'note': 'hi'},
])
def test_call_accepts_valid_arguments(toolset, arguments):
    """Arguments matching the schema reach the function."""
    assert call_tool(toolset, 'typed', arguments) == {'ok': True, 'output': 'ok'}


@pytest.mark.parametrize('arguments, reason', [
    ({}, "missing required argument(s): ['name']"),
    ({'name': 1}, "'name' must be string"),
    ({'name': 'x', 'count': 1.5}, "'count' must be integer"),
    ({'name': 'x', 'count': True}, "'count' must be integer"),
    ({'name': 'x', 'scale': '1'}, "'scale' must be number"),
    ({'name': 'x', 'flag': 1}, "'flag' must be boolean"),
    ({'name': 'x', 'tags': 'a'}, "'tags' must be array"),
    ({'name': 'x', 'mode': 'slow'}, "must be one of ['fast', 'best']"),
    ({'name': 'x', 'note': 3}, "'note' must be string or null"),
    ({'name': 'x', 'extra': 1}, "unknown argument 'extra'"),
])
def test_call_rejects_invalid_arguments_before_calling(toolset, arguments, reason):
    """Invalid arguments are reported without running the function."""
    result = call_tool(toolset, 'typed', arguments)
    assert result['ok'] is False
    assert reason in result['output']


def test_call_passes_extra_arguments_to_kwargs_functions(toolset):
    """A **kwargs function accepts arguments the schema does not list."""
    assert call_tool(toolset, 'with_kwargs', {'shot': 'sh010', 'quality': 'high'}) == {
        'ok': True, 'output': 'sh010'}


@pytest.mark.parametrize('name, reason', [
    ('missing', "Unknown tool 'missing'. Available: ['chatty', 'fails', 'typed', 'with_kwargs']"),
    ('broken', "Tool 'broken' was not loaded: cannot load"),
])
def test_call_unknown_or_skipped_tool_explains_why(toolset, name, reason):
    """The caller learns whether a tool never existed or failed to load."""
    result = call_tool(toolset, name, {})
    assert result['ok'] is False
    assert reason in result['output']


@pytest.mark.parametrize('arguments', [[1], 'text', 3])
def test_call_rejects_non_object_arguments(toolset, arguments):
    """Arguments must be a JSON object."""
    assert call_tool(toolset, 'chatty', arguments) == {
        'ok': False, 'output': 'Arguments must be a JSON object.'}


def test_call_with_no_arguments_uses_an_empty_object(toolset):
    """None counts as no arguments, so required ones are reported missing."""
    assert 'missing required' in call_tool(toolset, 'chatty')['output']


def test_annotations_are_kept_as_written(tool_file):
    """Clients use annotations, for example to skip approval for read-only tools."""
    hints = {'title': 'Publish', 'readOnlyHint': False, 'destructiveHint': False}
    toolset = load_tools(tool_file({'tools': [_tool(annotations=hints)]}))
    assert toolset.tools['publish_shot'].annotations == hints


def _snapshot(node=''):
    print(f'rendered {node or "viewer"}')
    return Image(b'\xff\xd8\xff')


SNAPSHOT = Tool('nuke_viewer_snapshot', 'See the Viewer.',
                {'type': 'object', 'properties': {'node': {'type': 'string'}}}, _snapshot)


def test_image_result_goes_to_images_as_base64():
    """An Image return value is sent as base64 next to what the tool printed."""
    toolset = ToolSet(builtins={SNAPSHOT.name: SNAPSHOT})
    assert call_tool(toolset, SNAPSHOT.name, {'node': 'Read1'}) == {
        'ok': True, 'output': 'rendered Read1\n',
        'images': [{'mimeType': 'image/jpeg', 'data': '/9j/'}]}


def test_builtins_are_listed_and_called_while_code_is_on(tool_file):
    """Built-in tools come before the tools file's and can be called."""
    toolset = load_tools(tool_file({'tools': [_tool()]}), {SNAPSHOT.name: SNAPSHOT})
    assert [t['name'] for t in list_tools(toolset)['tools']] == [SNAPSHOT.name, 'publish_shot']
    assert call_tool(toolset, SNAPSHOT.name)['ok'] is True


@pytest.mark.parametrize('content', [{'allow_arbitrary_code': False}, 'not json'])
def test_builtins_stay_when_code_is_off(tool_file, content):
    """Built-in tools have their own setting, so a locked-down tools file keeps them."""
    toolset = load_tools(tool_file(content), {SNAPSHOT.name: SNAPSHOT})
    assert [t['name'] for t in list_tools(toolset)['tools']] == [SNAPSHOT.name]
    assert call_tool(toolset, SNAPSHOT.name)['ok'] is True


def test_tools_file_cannot_replace_a_builtin(tool_file):
    """A tools file entry named like a built-in tool is skipped."""
    toolset = load_tools(tool_file({'tools': [_tool(name=SNAPSHOT.name)]}),
                         {SNAPSHOT.name: SNAPSHOT})
    assert 'already loaded' in toolset.skipped[SNAPSHOT.name]
    assert toolset.builtins[SNAPSHOT.name] is SNAPSHOT
