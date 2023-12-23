from __future__ import annotations

from typing import Any, Dict, TypeVar, Callable

R = TypeVar('R')
GenericFunc = Callable[..., R]

_CACHE: Dict[str, Dict[GenericFunc[Any], Any]] = {}


def cache(name: str) -> Callable[[GenericFunc[R]], GenericFunc[R]]:
    def inner(func: GenericFunc[R]) -> GenericFunc[R]:
        def wrapper(*args: Any, **kwargs: Any) -> R:
            if name not in _CACHE:
                _CACHE[name] = {}

            if func not in _CACHE[name]:
                _CACHE[name].update({func: func(*args, **kwargs)})

            return _CACHE[name][func]

        return wrapper

    return inner


def clear_cache(name: str):
    if name in _CACHE:
        _CACHE[name].clear()
