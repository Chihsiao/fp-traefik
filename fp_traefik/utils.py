__all__ = [
    'LeveledKv',
    'synchronized',
    'lazy',
]

import threading
from functools import wraps as func_wraps
from typing import TypeVar, Union, Tuple, Optional, Mapping, Iterable, Iterator, Callable

_T = TypeVar('_T')


class LeveledKv:
    Key, Value = str, Union[str, 'LeveledKV']
    Entry = Tuple[Key, Value]

    def __init__(self, mapping: Optional[Mapping[str, str]] = None):
        self._store = dict()
        if mapping is not None:
            for k, v in mapping.items():
                self[k] = v

    def keys(self) -> Iterable[Key]: return self._store.keys()
    def items(self) -> Iterable[Entry]: return self._store.items()

    def next_level(self, item: Key) -> 'LeveledKv':
        if not item.endswith('/'): item += '/'
        next_level = self._store.get(item)

        if next_level is None:
            next_level = LeveledKv()
            self._store[item] = next_level

        return next_level

    def locate(self, key: Key) -> Tuple['LeveledKv', str]:
        parent_kv = self
        is_namespace = key.endswith('/')
        basename = is_namespace and key[:-1] or key
        dirname, sep, basename = basename.partition('/')

        while sep:
            parent_kv = parent_kv.next_level(dirname)
            dirname, sep, basename = basename.partition('/')

        dirname, basename = None, dirname
        return parent_kv, basename + (is_namespace and '/' or '')

    def __getitem__(self, item: Key) -> Value:
        parent_kv, basename = self.locate(item)
        return (basename.endswith('/') and parent_kv.next_level(basename)
                or parent_kv._store.get(basename) or '')

    def __setitem__(self, key: Key, value: Value):
        parent_kv, basename = self.locate(key)
        parent_kv._store[basename] = value

    def flattened_items(self,
                        prefix: str = '',
                        only_extract: Optional[Iterable[str]] = None) -> Iterator[Tuple[str, str]]:
        stack = [(prefix + key, self[key]) for key in only_extract] \
            if only_extract is not None \
            else [(prefix, self),]

        while len(stack) > 0:
            prefix, kv = stack.pop()
            for key, value in kv.items():
                if key.endswith('/'):
                    new_prefix = prefix + key
                    frame = (new_prefix, value)
                    stack.append(frame)
                    continue

                yield prefix + key, value


def synchronized(lock=None):
    if lock is None: lock = threading.Lock()

    def decorator(func):
        @func_wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal lock
            with lock:
                return func(*args, **kwargs)

        return wrapper

    return decorator


def lazy(provider: Callable[[], _T]) -> Callable[[], _T]:
    result: Optional[_T] = None

    @func_wraps(provider)
    @synchronized()
    def wrapper():
        nonlocal result
        if result is None:
            result = provider()
        return result

    return wrapper
