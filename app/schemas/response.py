from pydantic import BaseModel
from typing import Any, Optional, TypeVar, Generic

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
    def success(data: Any = None, message: str = 'OK'):
        return Response(data=data, code=200, message=message)
