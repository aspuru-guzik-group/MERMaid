import os
from pathlib import Path
from openai import OpenAI
from prompt.builder import (
    build_guidelines
    , guidelines_to_str
    , apply_substitutions
)

MODULE_PATH = Path(__file__).resolve().parent
CODE_PATH = MODULE_PATH / "schema.py"
with open(CODE_PATH) as f:
    CODE_STR= f.read()


client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)


def build_prompt(
    s: str
) -> dict[str, str]:
    return {
        "role": "user"
        , "content": s
    }


def build_prompt_from_react(
    react_str: str
    , **kwargs
) -> dict[str,str]:
    return build_prompt(
        str(apply_substitutions(
            build_guidelines()
            , **{ "code": CODE_STR
              , "json": react_str
              , **kwargs
              }
        ))
    )


def build_prompt_from_react_file(
    path: Path | str
    , **kwargs
) -> dict[str, str]:
    with open(path, 'r') as f:
        return build_prompt_from_react(f.read(), **kwargs)


def get_response(
    messages: list[str]
) -> dict[str, str]:
    chat_completion = client.chat.completions.create(
        messages=messages
        , model="gpt-4o"
    )
    return {
        "role": "assistant"
        , "content": chat_completion.choices[0].message.content.strip()
    }
