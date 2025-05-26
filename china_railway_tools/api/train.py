import asyncio
import logging

from china_railway_tools.api.common import get_station, get_station_by_names, query_train_schedule
from china_railway_tools.schemas.query import *
from china_railway_tools.schemas.response import TrainTicketResponse
from china_railway_tools.schemas.station import Station
from china_railway_tools.schemas.train import *
from china_railway_tools.utils.DataStore import DataStore
from china_railway_tools.utils.cr_fetcher import fetch_trains
from china_railway_tools.utils.cr_utils import train_data_filter, filter_trains
from china_railway_tools.utils.decorators import validate_query_train

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

    stations = train_schedule.get_stations(form.from_station_name, form.to_station_name)
    if len(stations) <= 2:
        return []
    if form.partition >= len(stations) - 1:
        return [x.station_name for x in stations[1:-1]]

    durations = [stations[index + 1].get_arr_time_in_minute() - x.get_dep_time_in_minute() for index, x in
                 enumerate(stations[0:-1])]
    partitions = partition_array(durations, form.partition)
    break_points = [stations[x[1]].station_name for x in partitions[0:-1]]
    logger.info(f'{form.from_station_name}-{form.to_station_name}: Transfer stations: {','.join(break_points)}')
    return break_points


async def query_train_prices(form: QueryTrainTicket) -> TrainTicketResponse:
    """
    查询某车次指定区间分段购买的票价
    """
    query_train_form = QueryTrains(from_station_name=form.from_station_name, to_station_name=form.to_station_name,
                                   dep_date=form.dep_date, train_codes=[form.train_code], exact=True)
    trains = await query_tickets(query_train_form)
    if not trains:
        raise Exception('No trains found')
    elif len(trains) > 1:
        raise Exception(f'More than one train found, trains:{[t.model_dump() for t in trains]}')
    train: TrainInfo = trains[0]
    form.train_no = train.train_no
    train_date: datetime = train.get_train_date()
    train_schedule: TrainSchedule = await query_train_schedule(
        QueryTrainSchedule(train_date=train_date, train_no=form.train_no), )
    from_stop_info: StopInfo = train_schedule.get_stop_info(form.from_station_name)
    to_stop_info: StopInfo = train_schedule.get_stop_info(form.to_station_name)

    form.from_station_name = from_stop_info.station_name
    form.to_station_name = to_stop_info.station_name
    if from_stop_info is None or to_stop_info is None:
        raise Exception('The departure station or arrival station is not belongs to this train')
    if train_schedule.get_stop_index(from_stop_info.station_name) > train_schedule.get_stop_index(
            to_stop_info.station_name):
        raise Exception("The departure station must be before the arrival station")
    station_names = train_schedule.get_station_names(from_stop_info.station_name, to_stop_info.station_name)

    if form.partition >= 2:
        form.stop_stations = [*form.stop_stations, *divide_trip(train_schedule, form)]
    # filter assigned stop stations
    if len(form.stop_stations) > 0:
        station_names = [from_stop_info.station_name, *form.stop_stations, to_stop_info.station_name]
    stations = await get_station_by_names(station_names)
    if len(stations) != len(station_names):
        raise Exception(
            f'Query station result is not matched station names. Station names:{station_names} Result:{stations}')
    stations = [next((obj for obj in stations if obj.name == name), None) for name in station_names]

    async def ticket_task(_station: Station, _next_station: Station):
        dep_stop_info = train_schedule.get_stop_info(_station.name)
        q_ticket = QueryTrains(from_station_code=_station.code, to_station_code=_next_station.code,
                               dep_date=train_date + timedelta(days=dep_stop_info.get_dep_day_diff()), )
        train_info_list = await query_tickets(q_ticket)
        train_info_list = list(
            filter(lambda x: train_data_filter(x, from_code=_station.code, to_code=_next_station.code,
                                               train_no=form.train_no, ), train_info_list))
        if len(train_info_list) != 1:
            logger.warning(f'{_station}-{_next_station} ticket result is not expected, expect only one train')
            return None
        train_info: TrainInfo = train_info_list[0]
        train_info.from_stop_info = train_schedule.get_stop_info(_station.name)
        train_info.to_stop_info = train_schedule.get_stop_info(_next_station.name)
        return train_info

    tasks = []
    # query train_info from departure station to arrival station
    task = asyncio.create_task(ticket_task(stations[0], stations[-1]))
    tasks.append(task)
    for index, station in enumerate(stations[0:-1]):
        next_station = stations[index + 1]
        task = asyncio.create_task(ticket_task(station, next_station))
        tasks.append(task)

    # 使用 asyncio.gather 等待所有任务完成
    results = await asyncio.gather(*tasks)
    results = list(results)
    if not results:
        raise Exception("Fail to query tickets")
    response = TrainTicketResponse.from_raw_data(train_info=results[0], detail_trains=results[1:],
                                                 train_schedule=train_schedule)
    return response


@validate_query_train(get_station=get_station)
async def query_tickets(form: QueryTrains, **kwargs) -> List[TrainInfo]:
    ds = DataStore()
    dep_date_str = form.dep_date.strftime('%Y-%m-%d')
    train_info_list: List[TrainInfo] = []
    query_key = f'{form.from_station_code}-{form.to_station_code}-{dep_date_str}'

    if not form.force_update:
        train_info_list = ds.get(query_key)

    if train_info_list is None:
        train_info_list = await fetch_trains(form)
    elif isinstance(train_info_list, List) and len(train_info_list) == 0:
        return []

    if not train_info_list:
        ds.set([], query_key, 300)
        return []

    filtered_trains: List[TrainInfo] = filter_trains(form, train_info_list)
    filtered_trains = sorted(filtered_trains, key=lambda x: x.from_stop_info.dep_time if x.from_stop_info else None)
    return filtered_trains
