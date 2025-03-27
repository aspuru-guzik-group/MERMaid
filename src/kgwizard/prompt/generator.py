# -*- coding: utf-8 -*-
import os
from pathlib import Path
from typing import Any, Union

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

from .builder import (
    HEADER_PATH,
    INSTRUCTIONS_PATH,
    TAIL_PATH,
    apply_substitutions,
    build_guidelines,
)

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)


def build_prompt(
    s: str
) -> dict[str, str]:
    """
    Construct a prompt dictionary from a given string.

    :param s: The prompt content.
    :type s: str
    :return: A dictionary containing the role (`"user"`) and prompt content.
    :rtype: dict[str, str]
    """
    return {
        "role": "user"
        , "content": s
    }


def build_prompt_from_react(
    react_str: str
    , header_path: Union[None, str, Path] = HEADER_PATH
    , instructions_path: Union[None, str, Path] = INSTRUCTIONS_PATH
    , tail_path: Union[None, str, Path] = TAIL_PATH
    , **kwargs
) -> dict[str,str]:
    """
    Construct a prompt by applying template substitutions using a React-style JSON string.

    :param react_str: The React-style JSON string used for substitutions.
    :type react_str: str
    :param kwargs: Additional keyword arguments for template substitution.
    :type kwargs: dict[str, str]
    :return: A structured prompt dictionary.
    :rtype: dict[str, str]
    """
    return build_prompt(
        str(apply_substitutions(
            build_guidelines(
                header_path=header_path
                , instructions_path=instructions_path
                , tail_path=tail_path
            )
            , **{"json": react_str
              , **kwargs
              }
        ))
    )


def build_prompt_from_react_file(
    path: Union[str, Path]
    , header_path: Union[None, str, Path] = HEADER_PATH
    , instructions_path: Union[None, str, Path] = INSTRUCTIONS_PATH
    , tail_path: Union[None, str, Path] = TAIL_PATH
    , **kwargs
) -> dict[str, str]:
    """
    Read a React-style JSON file and construct a prompt with applied substitutions.

    :param path: The path to the JSON file.
    :type path: Path | str
    :param kwargs: Additional keyword arguments for template substitution.
    :type kwargs: dict[str, str]
    :return: A structured prompt dictionary.
    :rtype: dict[str, str]
    """
    with open(path, 'r') as f:
        return build_prompt_from_react(
            f.read()
            , header_path=header_path
            , instructions_path=instructions_path
            , tail_path=tail_path
            , **kwargs
        )


def get_response(
    messages: list[dict[str, Any]]
) -> dict[str, str]:
    """
    Send a list of messages to the OpenAI API and retrieve the assistant's response.

    :param messages: A list of message strings in conversation format.
    :type messages: list[str]
    :return: A dictionary containing the role (`"assistant"`) and response content.
    :rtype: dict[str, str]
    """
    chat_completion = client.chat.completions.create(
        messages=messages
        , model="gpt-4o"
    )
    return {
        "role": "assistant"
        , "content": chat_completion.choices[0].message.content.strip()
    }
