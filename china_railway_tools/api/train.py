import asyncio
import logging

from china_railway_tools.api.common import get_station, train_code2no, get_station_by_names, query_train_schedule
from china_railway_tools.schemas.query import *
from china_railway_tools.schemas.station import Station
from china_railway_tools.schemas.train import *
from china_railway_tools.utils.DataStore import DataStore
from china_railway_tools.utils.cr_fetcher import fetch_trains
from china_railway_tools.utils.cr_utils import filter_train_by_code, train_data_filter
from china_railway_tools.utils.decorators import validate_query_train, complete_train_no

logger = logging.getLogger(__name__)


def divide_trip(train_schedule: TrainSchedule, form: QueryTrainTicket):
    def partition_array(arr: List[int], N: int) -> list[tuple[int, int]]:
        """
        :author: ChatGPT-4o
        :param arr: Array to be divided
        :param N: Number of partitions
        :return: Divided segments contain start index and end index like [[0,2],[2,3]]
        """
        length = len(arr)

        # Calculate the approximate size of each segment
        avg_size = length // N
        extra = length % N

        current_index = 0
        indices = []
        for i in range(N):
            segment_size = avg_size + (1 if i < extra else 0)  # Some segments will be slightly larger
            start_index = current_index
            end_index = current_index + segment_size - 1
            indices.append((start_index, end_index + 1))
            current_index += segment_size

        return indices

    stations = train_schedule.get_stations(form.from_station, form.to_station)
    if len(stations) <= 2:
        return []
    if form.partition >= len(stations) - 1:
        return [x.station_name for x in stations[1:-1]]

    durations = [stations[index + 1].get_arr_time() - x.get_dep_time() for index, x in enumerate(stations[0:-1])]
    partitions = partition_array(durations, form.partition)
    break_points = [stations[x[1]].station_name for x in partitions[0:-1]]
    logger.info(f'{form.from_station}-{form.to_station}: Transfer stations: {','.join(break_points)}')
    return break_points


@complete_train_no(train_code2no=train_code2no)
async def query_train_prices(form: QueryTrainTicket):
    train_schedule: TrainSchedule = await query_train_schedule(
        QueryTrainSchedule(train_date=form.train_date, train_no=form.train_no), )
    if train_schedule.get_stop_info(form.from_station) is None or train_schedule.get_stop_info(
            form.to_station) is None:
        raise Exception('出发站或到达站不属于该次列车')
    station_names = train_schedule.get_station_names(form.from_station, form.to_station)

    if form.partition >= 2:
        form.stop_stations = [*form.stop_stations, *divide_trip(train_schedule, form)]
    # filter assigned stop stations
    if len(form.stop_stations) > 0:
        station_names = [form.from_station, *form.stop_stations, form.to_station]
    stations = await get_station_by_names(station_names)
    if len(stations) != len(station_names):
        raise Exception(
            f'Query station result is not matched station names. Station names:{station_names} Result:{stations}')
    stations = [next((obj for obj in stations if obj.name == name), None) for name in station_names]
    tickets = []

    async def ticket_task(_station: Station, _next_station: Station):
        q_ticket = QueryTrains(from_station_code=_station.code, to_station_code=_next_station.code,
                               dep_date=form.train_date)
        ticket = await query_tickets(q_ticket)
        _ticket = list(
            filter(lambda x: train_data_filter(x, form.train_no, _station.code, _next_station.code), ticket))
        if len(_ticket) != 1:
            logger.warning(f'{_station}-{_next_station} 车票结果不符合预期 {ticket}')
            return None
        return _ticket[0]

    tasks = []
    # query ticket from departure station to arrival station
    task = asyncio.create_task(ticket_task(stations[0], stations[-1]))
    tasks.append(task)
    for index, station in enumerate(stations[0:-1]):
        next_station = stations[index + 1]
        task = asyncio.create_task(ticket_task(station, next_station))
        tasks.append(task)

    # 使用 asyncio.gather 等待所有任务完成
    results = await asyncio.gather(*tasks)
    for result in results:
        if result is not None:
            tickets.append(result)

    return tickets


@validate_query_train(get_station=get_station)
async def query_tickets(form: QueryTrains, **kwargs) -> List[TrainInfo]:
    ds = DataStore()
    dep_date_str = form.dep_date.strftime('%Y-%m-%d')
    query_key = f'{form.from_station_code}-{form.to_station_code}-{dep_date_str}'
    train_info_list: List[TrainInfo] = ds.get(query_key)
    if train_info_list is None:
        train_info_list = await fetch_trains(form)
    elif isinstance(train_info_list, List) and len(train_info_list) == 0:
        return []

    if not train_info_list:
        ds.set([], query_key, 300)
        return []

    if len(form.train_codes) > 0:
        train_info_list = list(filter_train_by_code(train_info_list, form.train_codes))
    if len(form.stations) > 0:
        train_info_list = list(
            filter(lambda x: x.from_station in form.stations or x.to_station in form.stations, train_info_list))
    if form.exact and form.from_station_name and form.to_station_name:
        train_info_list = list(
            filter(lambda x: x.from_station == form.from_station_name and x.to_station == form.to_station_name,
                   train_info_list))
    return train_info_list
