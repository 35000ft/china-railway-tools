from functools import wraps
from typing import Callable

from fastapi import Response


def cache_control(max_age: int = 3600):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            response: Response = await func(*args, **kwargs)
            if isinstance(response, Response):
                response.headers["Cache-Control"] = f"public, max-age={max_age}"
            return response

        return wrapper

    return decorator
