from datetime import datetime
from typing import List, Optional, Dict

from pydantic import BaseModel, ConfigDict


class Ticket(BaseModel):
    stock: str
    seat_type: str
    price: str


class TrainInfo(BaseModel):
    depart_date: str
    train_date: str
    tickets: List[Ticket]
    from_station: str
    from_station_code: str
    to_station: str
    to_station_code: str
    train_code: str
    train_no: str
    first_station_code: str
    end_station_code: str

    def __hash__(self):
        # 使用 train_code 作为哈希值
        return hash((self.train_code, self.train_date, self.from_station, self.to_station))

    @classmethod
    def from_raw_dict(cls, depart_date: str, raw_data: dict):
        """
        :param depart_date: date of current station departure
        :param raw_data: raw data queried from 12306
        """
        return cls(
            depart_date=depart_date,
            train_date=datetime.strptime(raw_data['start_train_date'], '%Y%m%d').strftime('%Y-%m-%d'),
            train_no=raw_data['train_no'],
            train_code=raw_data['station_train_code'],
            tickets=[
                Ticket(
                    stock=x['stock'],
                    seat_type=x['seatType'],
                    price=str(x['price'])
                )
                for x in raw_data.get('prices', [])
            ],
            from_station=raw_data['from_station_name'],
            from_station_code=raw_data['from_station_telecode'],
            to_station=raw_data['to_station_name'],
            to_station_code=raw_data['to_station_telecode'],
            first_station_code=raw_data['start_station_telecode'],
            end_station_code=raw_data['end_station_telecode'],
        )


class TrainNo(BaseModel):
    id: int | None
    date: str
    train_no: str
    train_code: str
    from_station: str
    to_station: str
    model_config = ConfigDict(from_attributes=True)


class StopInfo(BaseModel):
    station_name: str
    arr_time: str
    dep_time: str
    stopover_time: int
    duration: str
    arr_day_diff: int
    station_train_code: str

    def get_duration(self):
        hours, minutes = map(int, self.duration.split(':'))
        return hours * 60 + minutes

    def get_arr_time(self):
        if self.arr_time == '----':
            return None
        hours, minutes = map(int, self.arr_time.split(':'))
        return hours * 60 + minutes

    def get_dep_time(self):
        if self.dep_time == '----':
            return None
        hours, minutes = map(int, self.dep_time.split(':'))
        return hours * 60 + minutes


class TrainSchedule(BaseModel):
    train_no: str
    train_date: str
    name_index: Dict[str, int]
    schedule: List[StopInfo]

    @classmethod
    def from_raw_dict(cls, raw_dict: dict, ):
        stop_info_list: List[StopInfo] = raw_dict.get('stop_info_list')
        return cls(
            train_no=raw_dict.get('train_no'),
            train_date=raw_dict.get('train_date'),
            schedule=stop_info_list,
            name_index={x.station_name: index for index, x in enumerate(stop_info_list)}
        )

    def get_stop_info(self, station_name: str) -> Optional[StopInfo]:
        index = self.name_index.get(station_name)
        if index is None:
            return None
        return self.schedule[index]

    def get_first(self) -> StopInfo:
        return self.schedule[0]

    def get_next(self, station_name) -> Optional[StopInfo]:
        index = self.name_index.get(station_name)
        if index is None:
            return None
        if index == len(self.schedule) - 1:
            return None
        return self.schedule[index + 1]

    def get_last(self) -> StopInfo:
        return self.schedule[-1]

    def get_station_names(self, from_station: str, to_station: str) -> List[str]:
        return [x.station_name for x in self.get_stations(from_station, to_station)]

    def get_stations(self, from_station: str, to_station: str) -> list[StopInfo]:
        from_station_index = self.name_index.get(from_station)
        if from_station_index is None:
            from_station_index = 0
        to_station_index = self.name_index.get(to_station)
        if to_station_index is None:
            to_station_index = len(self.schedule) - 1
        return self.schedule[from_station_index:to_station_index + 1]


class TrainTicket(BaseModel):
    train_no: str
    from_station: str
    to_station: str
    price: str

    def __init__(self, train_no, from_station, to_station, price, train_date):
        super().__init__(
            train_no=train_no,
            from_station=from_station,
            to_station=to_station,
        )
        self.train_no = train_no
        self.from_station = from_station
        self.to_station = to_station
        self.train_date = train_date
        self.price = price
