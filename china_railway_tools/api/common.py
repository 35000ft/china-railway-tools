import asyncio
import logging

from sqlalchemy import or_, func, and_
from sqlalchemy import select

from china_railway_tools.database.connection import AsyncSessionLocal
from china_railway_tools.database.curd import batch_add_train_no
from china_railway_tools.database.schema import MStation, MTrainNo, QueryResult
from china_railway_tools.schemas.query import QueryTrainSchedule
from china_railway_tools.schemas.station import Station
from china_railway_tools.schemas.train import *
from china_railway_tools.utils.cr_fetcher import fetch_train_no, fetch_train_schedule
from china_railway_tools.utils.decorators import complete_train_no

logger = logging.getLogger(__name__)


async def get_station_by_name(name: str) -> Optional[Station]:
    async with AsyncSessionLocal() as session:
        stmt = select(Station).where(MStation.name == name)
        result = await session.execute(stmt)
        station = result.scalars().one_or_none()
        if station is None:
            return None
        return Station.model_validate(station)


async def train_code2no(train_code: str, train_date: datetime = datetime.now()) -> Optional[str]:
    train_code_result = await query_train_no(train_code, train_date=train_date, exact=True)
    if len(train_code_result) == 0:
        return None
    filtered_result = list(filter(lambda r: r.train_code == train_code, train_code_result))
    return filtered_result[0].train_no if filtered_result else None


async def query_train_no(train_code: str, train_date: datetime = datetime.now(), **kwargs) -> List[TrainNo]:
    async with AsyncSessionLocal() as session:
        stmt = select(MTrainNo).filter(and_(
            MTrainNo.date == train_date.strftime('%Y-%m-%d'),
            MTrainNo.train_code == train_code if kwargs.get('exact', True)
            else MTrainNo.train_code.like(train_code + '%'))) \
            .order_by(func.length(MTrainNo.train_code), MTrainNo.train_code) \
            .limit(kwargs.get('limit', 200))
        _r = await session.execute(stmt)
        _r = _r.scalars().all()

    if len(_r) > 0:
        return [TrainNo.model_validate(x) for x in _r]

    train_no_model_list = await fetch_train_no(train_code, train_date.strftime('%Y-%m-%d'), **kwargs)
    _ = asyncio.create_task(batch_add_train_no(train_no_model_list, train_date))
    train_no_list: List[TrainNo] = [TrainNo.model_validate(x) for x in train_no_model_list]
    return train_no_list


async def get_station_by_names(names: List[str]) -> List[Station]:
    async with AsyncSessionLocal() as session:
        stmt = select(MStation).filter(MStation.name.in_(names))
        result = await session.execute(stmt)
        stations = result.scalars().all()
        stations = [Station.model_validate(x) for x in stations]
        return stations


async def get_station(code_or_name: str) -> Optional[Station]:
    async with AsyncSessionLocal() as session:
        stmt = select(MStation).where(or_(MStation.code == code_or_name, MStation.name == code_or_name))
        result = await session.execute(stmt)
        if r := result.scalars().one_or_none():
            return Station.model_validate(r)


@complete_train_no(train_code2no=train_code2no)
async def query_train_schedule(form: QueryTrainSchedule) -> Optional[TrainSchedule]:
    query_key = form.train_code if form.train_code is not None else form.train_no
    category = 'train_schedule'
    train_schedule: TrainSchedule = await fetch_train_schedule(form)
    async with AsyncSessionLocal() as session:
        t_r = QueryResult(date=form.train_date.strftime('%Y-%m-%d'), query_key=query_key, category=category,
                          result=train_schedule.model_dump_json())
        session.add(t_r)
        await session.commit()
    return train_schedule
