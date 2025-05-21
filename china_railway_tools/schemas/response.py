from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field

from china_railway_tools.schemas.train import TrainInfo, TrainSchedule


class TrainTicketResponse(BaseModel):
    train_info: TrainInfo
    detail_trains: List[TrainInfo] = Field([])
    total_price: Decimal
    raw_price: Decimal

    @classmethod
    def from_raw_data(cls, train_info: TrainInfo, detail_trains: List[TrainInfo],
                      train_schedule: TrainSchedule) -> 'TrainTicketResponse':
        train_info.stop_info_list = train_schedule.schedule
        if len(detail_trains) == 0:
            total_price = train_info.get_lowest_price()
        else:
            total_price = sum([x.get_lowest_price() for x in detail_trains])
        return cls(
            total_price=total_price,
            train_info=train_info,
            detail_trains=detail_trains,
            raw_price=train_info.get_lowest_price(),
        )
