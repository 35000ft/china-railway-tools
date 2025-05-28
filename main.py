import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler

from china_railway_tools.api.common import train_code2no, query_train_schedule
from china_railway_tools.api.train import query_tickets, query_train_prices
from china_railway_tools.database.curd import query_cached_result
from china_railway_tools.schemas.query import *
from china_railway_tools.schemas.train import TrainInfo


def setup_logging():
    print('init logging')
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    console_handler.setFormatter(console_fmt)
    root_logger.addHandler(console_handler)

    # 文件输出（可选：日志轮转）
    file_handler = RotatingFileHandler(
        filename='app.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        '%(asctime)s %(levelname)-5s %(name)-20s %(message)s'
    )
    file_handler.setFormatter(file_fmt)
    root_logger.addHandler(file_handler)


setup_logging()


async def main():
    # form: QueryTrains = QueryTrains(from_station_name='西安', to_station_name='西宁', exact=True,
    #                                 train_codes=['K1309'])
    # form: QueryTrainSchedule = QueryTrainSchedule(train_code='G7001')
    form: QueryTrainTicket = QueryTrainTicket(from_station_name='南京南', to_station_name='上海', train_code='G1', )
    # sc = await query_tickets(form)
    sc = await query_train_prices(form)
    # sc = await query_train_schedule(form)
    print(sc)
    # print(sc.model_dump_json())


if __name__ == '__main__':
    from china_railway_tools.schemas.station import Station
    from china_railway_tools.api.station import query_station

    asyncio.run(main())
