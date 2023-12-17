from __future__ import annotations

from typing import Any, Dict, TypeVar, Callable

R = TypeVar('R')
GenericFunc = Callable[..., R]

_CACHE: Dict[GenericFunc[Any], Any] = {}


def cache(func: GenericFunc[R]) -> GenericFunc[R]:
    def wrapper(*args: Any, **kwargs: Any) -> R:
        if func not in _CACHE:
            _CACHE[func] = func(*args, **kwargs)
        return _CACHE[func]
    return wrapper


def clear_cache():
    _CACHE.clear()
