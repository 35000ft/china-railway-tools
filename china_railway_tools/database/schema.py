import asyncio
import logging
from datetime import datetime
from typing import Self

from .connection import Base, async_engine
from sqlalchemy import Column, Integer, String, DateTime, func, Date, UniqueConstraint, TEXT

logger = logging.getLogger(__name__)


class MStation(Base):
    __tablename__ = 'tb_station'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    pinyin = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    pinyin_abbr = Column(String, nullable=False, index=True)
    city = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    modified_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class MTrainNo(Base):
    __tablename__ = 'tb_train_no'

    id = Column(Integer, primary_key=True)
    date = Column(TEXT, nullable=False)
    train_no = Column(String, nullable=False)
    train_code = Column(String, nullable=False)
    from_station = Column(String, nullable=False)
    to_station = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    modified_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    __table_args__ = (
        UniqueConstraint('date', 'train_code', name='uix_date_train_code'),
    )

    @classmethod
    def to_train_no(cls, _d: dict) -> Self:
        return MTrainNo(train_no=_d['train_no'], train_code=_d['station_train_code'],
                        date=datetime.strptime(_d['date'], '%Y%m%d').strftime("%Y-%m-%d"),
                        from_station=_d['from_station'], to_station=_d['to_station'])


class QueryResult(Base):
    __tablename__ = 'tb_query_result'

    id = Column(Integer, primary_key=True)
    date = Column(String, nullable=False)
    query_key = Column(String, nullable=False)
    category = Column(String, nullable=False)
    result = Column(TEXT, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


async def init_db_async():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def init_db():
    logger.info('initializing database...')
    try:
        loop = asyncio.get_event_loop()

        if loop.is_running():
            asyncio.ensure_future(init_db_async())
        else:
            asyncio.run(init_db_async())
    except RuntimeError as e:
        print(f"Error: {e}")
        asyncio.run(init_db_async())
    logger.info('database initialized.')
