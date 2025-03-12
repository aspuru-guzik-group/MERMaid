# -*- coding: utf-8 -*-
"""
Module to build the prompt for graph parsing.

This module provides utilities for constructing structured prompts using predefined
headers, instructions, and tails stored in text files. It supports dynamic text
substitution and ensures proper formatting for guideline generation.

Constants:
----------
- `MODULE_PATH`: The absolute path of the current module.
- `ASSETS_PATH`: The directory containing prompt assets.
- `HEADER_PATH`: Default path to the header file.
- `INSTRUCTIONS_PATH`: Default path to the instructions file.
- `TAIL_PATH`: Default path to the tail file.

Types:
------
- `Header`: A new type representing the header string.
- `Tail`: A new type representing the tail string.
- `Instructions`: A list of instruction strings.

Classes:
--------
- `Guidelines`: A named tuple representing structured guidelines with a header,
  a list of instructions, and a tail.
"""
from typing import NewType, NamedTuple, Union
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
    """
    A structured representation of guidelines consisting of a header,
    a list of instructions, and a tail.

    :param header: The header section of the guidelines.
    :type header: Header | None
    :param instructions: A list of instruction strings.
    :type instructions: list[str]
    :param tail: The tail section of the guidelines.
    :type tail: Tail | None
    """
    header: Union[Header, None]
    instructions: list[str]
    tail: Tail | None

    def __str__(self):
        return guidelines_to_str(self)


def subs_or_none(
    s: str
    , **kwargs
) -> Union[str, None]:
    """
    Perform string substitution with placeholders.

    :param s: The string containing placeholders.
    :type s: str
    :param kwargs: Key-value pairs for substitution.
    :return: The formatted string or `None` if a key is missing.
    :rtype: str | None
    """
    try:
        return s.format(**kwargs)
    except KeyError: 
        return None

    
def subs_or_still(
    s: str
    , **kwargs
) -> str:
    """
    Perform string substitution with placeholders, keeping the original
    string if a key is missing.

    :param s: The string containing placeholders.
    :type s: str
    :param kwargs: Key-value pairs for substitution.
    :return: The formatted string, or the original string if a key is missing.
    :rtype: str
    """
    try: return s.format(**kwargs)
    except KeyError: 
        return s


def apply_substitutions(
    guidelines: Guidelines
    , remove_not_found_tokens: bool=True
    , **kwargs: dict[str, str]
) -> Guidelines:
    """
    Apply keyword-based substitutions to a `Guidelines` object.

    :param guidelines: The `Guidelines` object to be processed.
    :type guidelines: Guidelines
    :param remove_not_found_tokens: If `True`, removes tokens that have no matching key.
    :type remove_not_found_tokens: bool, optional
    :param kwargs: Key-value pairs for substitution.
    :type kwargs: dict[str, str]
    :return: A new `Guidelines` object with substitutions applied.
    :rtype: Guidelines
    """
    f = subs_or_none if remove_not_found_tokens else subs_or_still
    return Guidelines(
        header=None if guidelines.header is None else Header(f(guidelines.header, **kwargs))
        , instructions=[x for x in (f(i, **kwargs) for i in guidelines.instructions) if x is not None]
        , tail=None if guidelines.tail is None else Tail(f(guidelines.tail, **kwargs))
    )


def guidelines_to_str(
    g: Guidelines
) -> str:
    """
    Convert a `Guidelines` object into a formatted string.

    :param g: The `Guidelines` object to convert.
    :type g: Guidelines
    :return: A formatted string representation of the guidelines.
    :rtype: str
    """
    return (
        (g.header or '') + '\n\n'
        + '\n'.join(g.instructions) + '\n\n'
        + (g.tail or '' + '\n'))


def build_header(
    path: Union[str, Path]=HEADER_PATH
) -> Header:
    """
    Read and return the content of the header file.

    :param path: Path to the header file.
    :type path: str | Path, optional
    :return: The content of the header file.
    :rtype: Header
    """
    with open(path, 'r', encoding="utf-8") as f:
        return Header(f.read())


def build_tail(
    path: Union[str, Path]=TAIL_PATH
) -> Tail:
    """
    Read and return the content of the tail file.

    :param path: Path to the tail file.
    :type path: str | Path, optional
    :return: The content of the tail file.
    :rtype: Tail
    """
    with open(path, 'r', encoding="utf-8") as f:
        return Tail(f.read())

def build_instructions(
    path: Union[str, Path]=INSTRUCTIONS_PATH
) -> Instructions:
    """
    Read and return the list of instructions from the instructions file.

    :param path: Path to the instructions file.
    :type path: str | Path, optional
    :return: A list of instructions extracted from the file.
    :rtype: Instructions
    """
    with open(path, 'r', encoding="utf-8") as f:
        return Instructions([l.strip() for l in f if l.startswith('-')])

def build_guidelines(
    header_path: Union[None, str, Path]=HEADER_PATH
    , instructions_path: Union[None, str, Path]=INSTRUCTIONS_PATH
    , tail_path: Union[None, str, Path]=TAIL_PATH
) -> Guidelines:
    """
    Construct a `Guidelines` object from optional file paths.

    :param header_path: Path to the header file. If `None`, no header is used.
    :type header_path: None | str | Path, optional
    :param instructions_path: Path to the instructions file. If `None`, no instructions are used.
    :type instructions_path: None | str | Path, optional
    :param tail_path: Path to the tail file. If `None`, no tail is used.
    :type tail_path: None | str | Path, optional
    :return: A `Guidelines` object containing the loaded sections.
    :rtype: Guidelines
    """
    return Guidelines(
        header = None if not header_path else build_header(header_path)
        , instructions = None if not instructions_path else build_instructions(instructions_path)
        , tail = None if not tail_path else build_tail(tail_path)
    )
