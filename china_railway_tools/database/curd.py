import json
from datetime import datetime, timedelta
from typing import List

from pydantic import BaseModel
from sqlalchemy import select, and_

from china_railway_tools.database.connection import AsyncSessionLocal
from china_railway_tools.database.schema import MTrainNo, QueryResult
from china_railway_tools.utils.decorators import validate_date_param
from china_railway_tools.utils.serialization_utils import to_json, to_obj


async def batch_add_train_no(train_no_list: List[MTrainNo], train_date: datetime):
    train_codes = {x.train_code for x in train_no_list}
    async with AsyncSessionLocal() as session:
        stmt = select(MTrainNo).filter(and_(
            MTrainNo.date == train_date.strftime('%Y-%m-%d'),
            MTrainNo.train_code.in_(train_codes)))
        result = await session.execute(stmt)
        existed_train_no: List[MTrainNo] = result.scalars().all()
        excluded_codes = {x.train_code for x in existed_train_no}
        filtered_train_no_list = filter(lambda x: x.train_code not in excluded_codes, train_no_list)
        session.add_all(filtered_train_no_list)
        await session.commit()


@validate_date_param(date_param_name='_date')
async def query_cached_result(query_key: str, category: str, empty_cb, expire: int = None, **kwargs):
    _date: str = kwargs.get('_date')
    async with AsyncSessionLocal() as session:
        stmt = select(QueryResult).filter(and_(
            QueryResult.query_key == query_key,
            QueryResult.category == category,
            QueryResult.date == _date,
        ))
        result = await session.execute(stmt)
        cached: QueryResult = result.scalars().first()
        now = datetime.utcnow()

        # 检查是否存在缓存且未过期
        if cached:
            if expire is not None:
                expire_time = cached.created_at + timedelta(minutes=expire)
                if now >= expire_time:
                    # 删除过期记录
                    await session.delete(cached)
                    await session.commit()
                    cached = None
            else:
                return to_obj(cached.result, kwargs.get('pydantic_class'))

        # 如果没有缓存或已过期，调用回调生成
        if not cached:
            new_data = await empty_cb()
            if new_data:
                query_result = QueryResult(
                    query_key=query_key,
                    category=category,
                    date=_date,
                    result=json.dumps(to_json(new_data), ensure_ascii=False),
                )
                session.add(query_result)
                await session.commit()
                return new_data
            else:
                return None
        return to_obj(cached.result, kwargs.get('pydantic_class'))
