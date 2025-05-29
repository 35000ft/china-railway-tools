from pydantic import BaseModel
from typing import Any, Optional, TypeVar, Generic
from fastapi.responses import JSONResponse

T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    code: int
    message: str
    data: Optional[T]

    def __init__(self, code: int, message: str, data: Optional[Any], **kwargs):
        super().__init__(
            data=data,
            code=code,
            message=message,
            **kwargs)

    @staticmethod
    def gen_response(data: Any = None) -> JSONResponse:
        if data is None:
            return JSONResponse(content={'message': 'not found'}, status_code=400)
        if isinstance(data, BaseModel):
            content = data.model_dump()
        elif isinstance(data, list) and all(isinstance(item, BaseModel) for item in data):
            content = [item.model_dump() for item in data]
        else:
            content = data
        return JSONResponse(content=content, status_code=200)
