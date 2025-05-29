import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import List

from sqlalchemy import select, func, delete
from sqlalchemy.dialects.sqlite import insert

from china_railway_tools.config import get_config
from china_railway_tools.database.connection import AsyncSessionLocal
from china_railway_tools.database.schema import MStation, MTrainNo, QueryResult, init_db_async
from china_railway_tools.schemas.station import Station
from china_railway_tools.utils.cr_fetcher import fetch_all_stations
from china_railway_tools.utils.exception_utils import extract_exception_traceback

logger = logging.getLogger(__name__)


async def main():
    await init_db_async()
    await check_update_stations()
    if get_config('auto_clean_train_no'):
        await clean_train_no()
    await clean_cache_result()


async def check_update_stations():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(func.count()).select_from(MStation))
            cur_station_count = result.scalar_one()
            stations: List[Station] = await fetch_all_stations()
            if cur_station_count == len(stations):
                return
            logger.info('Updating stations')
            if cur_station_count == 0:
                await init_stations(stations)
            else:
                await update_stations(stations)
            logger.info(f'ALL Stations are up to date, total:{len(stations)}')
    except Exception as e:
        logger.warning(f'Failed to check update stations: {extract_exception_traceback(e)}')


async def init_stations(stations) -> List[Station]:
    if not stations:
        stations = await fetch_all_stations()
    async with AsyncSessionLocal() as session:
        station_models: List[MStation] = [MStation(**x.model_dump()) for x in stations]
        session.add_all(station_models)
        await session.commit()
        return stations


async def update_stations(stations: List[Station] = None) -> List[Station]:
    if not stations:
        stations = await fetch_all_stations()
    async with AsyncSessionLocal() as session:
        payloads = [x.model_dump() for x in stations]
        base_stmt = insert(MStation).values(payloads)
        stmt = (
            base_stmt.on_conflict_do_update(
                index_elements=[MStation.code],
                set_={  # 冲突时要更新的列
                    MStation.name: base_stmt.excluded.name,
                    MStation.pinyin: base_stmt.excluded.pinyin,
                    MStation.pinyin_abbr: base_stmt.excluded.pinyin_abbr,
                    MStation.city: base_stmt.excluded.city,
                }
            )
        )
        await session.execute(stmt)

        await session.commit()
        return stations


async def clean_train_no():
    async with AsyncSessionLocal() as session:
        max_days = get_config('max_saved_train_no_days', 7)
        target_date: date = (datetime.now() - timedelta(days=max_days)).date()
        target_date: str = target_date.strftime('%Y-%m-%d')
        async with session.begin():
            await session.execute(
                delete(MTrainNo).where(MTrainNo.date < target_date)
            )


async def clean_cache_result():
    async with AsyncSessionLocal() as session:
        max_days = get_config('max_cached_days', 3)
        target_date: datetime = (datetime.now() - timedelta(days=max_days))
        async with session.begin():
            await session.execute(
                delete(QueryResult).where(QueryResult.created_at < target_date)
            )


def run():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            task = loop.create_task(main())
            loop.run_until_complete(task)
        else:
            asyncio.run(main())
    except RuntimeError as e:
        logger.error(f'china_railway_tools initialization error: {extract_exception_traceback(e)}')
