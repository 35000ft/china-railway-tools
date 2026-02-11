import ast
import json
from json import JSONDecodeError
from typing import Any, TypeVar, Annotated

from pydantic import AfterValidator, BeforeValidator
from pydantic_core import PydanticUseDefault


def default_if_none(value: Any) -> Any:
    if value is None:
        raise PydanticUseDefault()
    return value


def fix_list_args(v):
    if isinstance(v, str) and v.startswith("[") and v.endswith("]"):
        # Try to use json decode: support input like "[\"test\"]"
        try:
            j_obj = json.loads(v)
            if isinstance(j_obj, list):
                return j_obj
            else:
                raise ValueError("Argument is not a list")
        except JSONDecodeError:
            pass

        # Try to use eval decode: support input like "['A', 'B', 'C']"
        return ast.literal_eval(v)
    elif isinstance(v, list):
        return v
    return None


T = TypeVar('T')
DefaultIfNone = Annotated[T | None, AfterValidator(default_if_none)]
ListArgs = Annotated[list[T] | None, BeforeValidator(fix_list_args)]
