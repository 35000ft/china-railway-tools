import functools
from datetime import datetime
from typing import Callable

from china_railway_tools.schemas.query import QueryTrains


def validate_query_train(get_station: Callable) -> Callable:
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(form: QueryTrains, *args, **kwargs):
            # 在调用目标函数前进行校验/转换
            await form.parse_station_name2code(get_station)
            # 执行被装饰的函数
            return await func(form, *args, **kwargs)

        return wrapper

    return decorator


def complete_train_no(train_code2no, train_code_attr_name='train_code', train_date_attr_name='train_date',
                      train_no_attr_name='train_no'):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(form, *args, **kwargs):
            if isinstance(form, dict):
                train_date = form.get(train_date_attr_name) or datetime.now()
                train_code = form.get(train_code_attr_name)
                train_no = form.get(train_no_attr_name)
            elif hasattr(form, train_code_attr_name) and hasattr(form, train_date_attr_name):
                train_date = getattr(form, train_date_attr_name, None) or datetime.now()
                train_code = getattr(form, train_code_attr_name)
                train_no = getattr(form, train_no_attr_name)
            else:
                raise TypeError(f'form must be dict or object with expected attributes, type:{type(form)}')
            if not train_no:
                train_no = await train_code2no(train_code, train_date)
                if not train_no:
                    raise Exception('failed to complete train no')
                else:
                    if isinstance(form, dict):
                        form[train_no_attr_name] = train_no
                    elif hasattr(form, train_code_attr_name) and hasattr(form, train_date_attr_name):
                        setattr(form, train_no_attr_name, train_no)
            return await func(form, *args, **kwargs)

        return wrapper

    return decorator


def validate_date_param(date_param_name: str):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if date_param_name not in kwargs:
                raise Exception('date param must be in kwargs')
            date_value = kwargs.get(date_param_name)
            if isinstance(date_value, datetime):
                date_value = date_value.strftime('%Y-%m-%d')
            elif isinstance(date_value, str):
                date_value = datetime.strptime(date_value, '%Y-%m-%d').strftime('%Y-%m-%d')
            else:
                raise TypeError("_date must be datetime or str")
            kwargs[date_param_name] = date_value
            return await func(*args, **kwargs)

        return wrapper

    return decorator
