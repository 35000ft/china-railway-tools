from datetime import datetime, timedelta
from typing import Optional, Callable, Awaitable, List, Set

from pydantic import BaseModel, Field, model_validator

from china_railway_tools.schemas.station import Station
from china_railway_tools.utils.str_utils import is_not_blank, is_blank


class QueryTrains(BaseModel):
    from_station_code: Optional[str] = Field(None, title="出发站电报码", description='广州南', max_length=100)
    from_station_name: Optional[str] = Field(None, title="出发站名", description='广州南', max_length=100)
    to_station_code: Optional[str] = Field(None, title="到达站电报码", description='阳江', max_length=100)
    to_station_name: Optional[str] = Field(None, title="到达站名", description='阳江', max_length=100)
    dep_date: datetime = Field((datetime.now() + timedelta(days=1)), title="出发日期")
    train_codes: List[str] = Field([], title='筛选车次')
    stations: List[str] = Field([], title='筛选车站')
    force_update: bool = Field(False, title="是否强制更新", description='是否强制更新(不查询缓存)', )
    exact: bool = Field(False, title="是否精确站名", description='是否精确站名', )

    async def parse_station_name2code(self, parser: Callable[[str], Awaitable[Station]]):
        if is_not_blank(self.from_station_name) and is_blank(self.from_station_code):
            station = await parser(self.from_station_name)
            if station is None:
                raise Exception(f'No from_station named {self.from_station_name}')
            self.from_station_code = station.code
        if is_not_blank(self.to_station_name) and is_blank(self.to_station_code):
            station = await parser(self.to_station_name)
            if station is None:
                raise Exception(f'No to_station named {self.to_station_name}')
            self.to_station_code = station.code


class QueryTrainSchedule(BaseModel):
    train_date: datetime = Field((datetime.now() + timedelta(days=1)))
    train_code: Optional[str] = Field(default=None, title='列车车次', max_length=10)
    train_no: Optional[str] = Field(default=None, title='列车编号', max_length=50)

    @classmethod
    @model_validator(mode='before')
    def validate_train_no_and_code(cls, values):
        train_no = values.get('train_no')
        train_code = values.get('train_code')
        if not train_no and not train_code:
            raise ValueError("Either 'train_no' or 'train_code' is required.")
        return values


class QueryTrainSchedules(BaseModel):
    train_condition: Optional[QueryTrains] = Field(title="车次条件")
    train_date: datetime = Field((datetime.now() + timedelta(days=1)))
    train_codes: List[str] = Field(default=[], title='列车车次')
    via_stations_and: List[str] = Field(default=[], title='车次必须经停这些车站')
    via_stations_or: List[str] = Field(default=[], title='车次必须经停这些车站之一')

    @classmethod
    @model_validator(mode='before')
    def validate_via_stations(cls, values):
        via_stations_or = values.get('via_stations_or')
        via_stations_and = values.get('via_stations_and')
        if via_stations_and and via_stations_or:
            if len(via_stations_and) >= len(via_stations_or) > 0:
                raise ValueError("via_stations_and不能和via_stations_or同时存在")
        return values


class QueryTrainTicket(BaseModel):
    from_station: str = Field('广州南', title="出发站名", max_length=100)
    to_station: str = Field('南京南', title="到达站名", max_length=100)
    train_date: datetime = (datetime.now() + timedelta(days=1))
    train_no: Optional[str] = Field(None, title='列车编号', max_length=10)
    train_code: Optional[str] = Field(None, title='列车车次', max_length=10)
    stop_stations: Optional[Set[str]] = Field([], title='分段购票换乘站')
    partition: Optional[int] = Field(-1, title='分段购票段数')

    @model_validator(mode='before')
    def validate_train_no_and_code(cls, values):
        train_no = values.get('train_no')
        train_code = values.get('train_code')
        if not train_no and not train_code:
            raise ValueError("Either 'train_no' or 'train_code' is required.")
        return values
