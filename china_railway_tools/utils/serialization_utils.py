import json
from typing import Type

from pydantic import BaseModel


def to_json(_obj: dict | BaseModel):
    if isinstance(_obj, BaseModel):
        return _obj.model_dump_json()
    elif isinstance(_obj, dict):
        return json.dumps(_obj, ensure_ascii=False)
    return json.dumps(_obj, ensure_ascii=False)


def to_obj(_obj: dict | str, pydantic_class: Type[BaseModel]) -> BaseModel:
    if isinstance(_obj, str):
        _obj = json.loads(_obj)
    return pydantic_class(**_obj)
