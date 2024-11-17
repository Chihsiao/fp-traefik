__all__ = [
    'raw_literal',
    'invoke',
    'not_match',
    'match_all',
    'match_any',
    'host',
    'path_prefix',
]

from typing import Iterable


def raw_literal(value: str) -> str:
    assert '`' not in value, 'raw literal should not contain `'
    return f'`{value}`'


def invoke(func: str, *args: str) -> str:
    return f'{func}({', '.join(args)})'


def not_match(predicate: str) -> str:
    return predicate and f'!({predicate})' or ''


def match_all(predicates: Iterable[str]) -> str:
    return ' && '.join(f'({p})' for p in predicates if p)


def match_any(predicates: Iterable[str]) -> str:
    return ' || '.join(f'({p})' for p in predicates if p)


def host(value: str) -> str:
    return invoke('Host', raw_literal(value))


def path_prefix(value: str) -> str:
    return invoke('PathPrefix', raw_literal(value))
