from __future__ import annotations

from typing import Any, Dict, TypeVar, Callable, Optional

R = TypeVar('R')
GenericFunc = Callable[..., R]

_CACHE: Dict[str, Dict[str, Any]] = {}


def cache(name: str) -> Callable[[GenericFunc[R]], GenericFunc[R]]:
    def inner(func: GenericFunc[R]) -> GenericFunc[R]:
        def wrapper(*args: Any, **kwargs: Any) -> R:
            if name not in _CACHE:
                _CACHE[name] = {}

            func_name = func.__name__
            if func_name not in _CACHE[name]:
                _CACHE[name][func_name] = func(*args, **kwargs)

            return _CACHE[name][func_name]

        return wrapper

    return inner


def clear_cache(name: str):
    if name in _CACHE:
        _CACHE[name].clear()
