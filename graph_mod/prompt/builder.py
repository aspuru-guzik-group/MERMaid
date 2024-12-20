# -*- coding: utf-8 -*-
"""Module to build the prompt for graph parsing"""
from typing import NewType, NamedTuple
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent
ASSETS_PATH = MODULE_PATH/"assets"
HEADER_PATH = ASSETS_PATH/"header"
INSTRUCTIONS_PATH = ASSETS_PATH/"instructions"
TAIL_PATH = ASSETS_PATH/"tail"

Header = NewType("Header", str)
Tail = NewType("Tail", str)
Instructions = NewType("Instructions", list[str])


class Guidelines(NamedTuple):
    header: Header | None
    instructions: list[str]
    tail: Tail | None

    def __str__(self):
        return guidelines_to_str(self)

def subs_or_none(
    s: str
    , **kwargs
) -> str | None:
    try:
        return s.format(**kwargs)
    except KeyError: return None

def subs_or_still(
    s: str
    , **kwargs
) -> str:
    try: return s.format(**kwargs)
    except KeyError: return s


def apply_substitutions(
    guidelines: Guidelines
    , remove_not_found_tokens: bool=True
    , **kwargs: dict[str, str]
) -> Guidelines:
    f = subs_or_none if remove_not_found_tokens else subs_or_still
    return Guidelines(
        header=None if guidelines.header is None else Header(f(guidelines.header, **kwargs))
        , instructions=[x for x in (f(i, **kwargs) for i in guidelines.instructions) if x is not None]
        , tail=None if guidelines.tail is None else Tail(f(guidelines.tail, **kwargs))
    )


def guidelines_to_str(
    g: Guidelines
) -> str:
    return (
        (g.header or '') + '\n\n'
        + '\n'.join(g.instructions) + '\n\n'
        + (g.tail or '' + '\n'))


def build_header(
    path: str | Path=HEADER_PATH
) -> Header:
    with open(path, 'r', encoding="utf-8") as f:
        return Header(f.read())


def build_tail(
    path: str | Path=TAIL_PATH
) -> Tail:
    with open(path, 'r', encoding="utf-8") as f:
        return Tail(f.read())

def build_instructions(
    path: str | Path=INSTRUCTIONS_PATH
) -> Instructions:
    with open(path, 'r', encoding="utf-8") as f:
        return Instructions([l.strip() for l in f if l.startswith('-')])

def build_guidelines(
    header_path: None | str | Path=HEADER_PATH
    , instructions_path: None | str | Path=INSTRUCTIONS_PATH
    , tail_path: None | str | Path=TAIL_PATH

) -> Guidelines:
    return Guidelines(
        header = None if not header_path else build_header(header_path)
        , instructions = None if not instructions_path else build_instructions(instructions_path)
        , tail = None if not tail_path else build_tail(tail_path)
    )
