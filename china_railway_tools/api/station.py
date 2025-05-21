import re
from typing import List

from sqlalchemy import or_, select

from china_railway_tools.database.connection import AsyncSessionLocal
from china_railway_tools.database.schema import MStation
from china_railway_tools.schemas.station import Station


async def query_station(keyword: str, **kwargs) -> List[Station]:
    keyword = keyword.strip()
    if keyword == '':
        return []
    limit = min(kwargs.get('limit', 500), 500)
    async with AsyncSessionLocal() as session:
        if kwargs.get('exact', False):
            stmt = select(MStation).where(or_(
                MStation.name == keyword,
                MStation.code == keyword,
            ))
        else:
            # 根据英文名(拼音)查询
            if re.match(r'^[a-zA-Z]+', keyword):
                stmt = select(MStation).where(
                    or_(
                        MStation.pinyin.like(f'%{keyword}%'),
                        MStation.pinyin_abbr.like(f'%{keyword}%')
                    )
                ).limit(limit)

            # 根据城市或者站名查询
            else:
                stmt = select(MStation).where(
                    or_(
                        MStation.city.startswith(keyword),
                        MStation.name.like(f'%{keyword}%')
                    )
                ).limit(limit)

        result = await session.execute(stmt)
        station_models = result.scalars().all()
        stations: List[Station] = [Station.model_validate(x) for x in station_models]
        return stations
