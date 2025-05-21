from datetime import datetime
from typing import List

from sqlalchemy import select, and_

from china_railway_tools.database.connection import AsyncSessionLocal
from china_railway_tools.database.schema import MTrainNo


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
