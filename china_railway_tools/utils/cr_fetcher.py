import asyncio
import logging
import time
import urllib.parse
from datetime import datetime
from typing import Callable, Awaitable, List

from lxml import html

from china_railway_tools.config import get_config
from china_railway_tools.database.schema import MTrainNo
from china_railway_tools.schemas.station import Station
from china_railway_tools.schemas.train import TrainSchedule
from china_railway_tools.utils import exception_utils
from china_railway_tools.utils.DataStore import DataStore
from china_railway_tools.utils.cr_utils import parse_ticket_data, parse_stop_info_list
from china_railway_tools.utils.http_utils import HeadersBuilder, get_async_client

logger = logging.getLogger(__name__)

FETCH_URLS = {
    # GET 查询余票
    'QUERY_TICKETS': 'https://kyfw.12306.cn/otn/leftTicket/queryG',
    # POST 获取cookies
    'GET_COOKIES': 'https://www.12306.cn/index/otn/login/conf',
    # GET 查询余票
    'QUERY_TRAIN_SCHEDULE': 'https://kyfw.12306.cn/otn/queryTrainInfo/query',
    # query train no by train code. like train code:Z39 -> train no:9300000Z4209
    'QUERY_TRAIN_NO': 'https://search.12306.cn/search/v1/train/search',
}
data_store: DataStore = DataStore()

fetch_cookie_semaphore = asyncio.Semaphore()


class CookieStore:
    def __init__(self, timeout: int, _fetch_cookie: Callable[[], Awaitable[str]]):
        self.timeout = timeout  # 设定cookie过期时间
        self.cookie = None  # 存储cookie
        self.cookie_time = None  # 存储cookie获取的时间
        self.cookie_getter = _fetch_cookie
        self.logger = logger

    def is_cookie_expired(self):
        if self.cookie is None or self.cookie_time is None:
            return True
        return time.time() - self.cookie_time > self.timeout

    async def get_valid_cookie(self):
        async with fetch_cookie_semaphore:
            if self.is_cookie_expired():
                self.logger.info("Cookie expired, fetching...")
                self.cookie = await self.cookie_getter()
                self.cookie_time = time.time()  # 更新获取cookie的时间
            return self.cookie


COOKIE_STORE = None
store_semaphore = asyncio.Semaphore()


def get_url(key: str):
    return FETCH_URLS.get(key)


async def get_semaphore(key: str, max_concurrency: int = None) -> bool:
    key_path = f'check.query.{key}'
    semaphore = data_store.get(key_path)
    max_concurrency = get_config(f'fetch_concurrency.{key}', max_concurrency or 5)
    if not semaphore:
        semaphore = asyncio.Semaphore(max_concurrency)
        data_store.set(semaphore, key_path=key_path, ttl_seconds=86400)
    return semaphore


async def fetch_cookie() -> str:
    _url = get_url('GET_COOKIES')
    async with get_async_client() as client:
        _headers = HeadersBuilder() \
            .add_header('Referer', 'https://www.12306.cn/index/') \
            .add_header('X-Requested-With', 'XMLHttpRequest') \
            .add_header('Content-Length', '0').build()
        response = await client.get(_url + "?t=" + str(int(time.time())), headers=_headers, follow_redirects=False)
        cookie_list = response.headers.raw
        _cookies = ';'.join([x[1].decode() for x in cookie_list if x[0].decode().lower() == 'set-cookie'])
        return _cookies


async def get_cookie_store() -> CookieStore:
    global COOKIE_STORE
    async with store_semaphore:
        if not COOKIE_STORE:
            COOKIE_STORE = CookieStore(60 * 180, fetch_cookie)
        return COOKIE_STORE


async def fetch_trains(form, **kwargs) -> list:
    semaphore = await get_semaphore('fetch_trains')
    async with semaphore:
        _url = get_url('QUERY_TICKETS')
        _params = {
            'leftTicketDTO.train_date': form.dep_date.strftime('%Y-%m-%d'),
            'leftTicketDTO.from_station': form.from_station_code,
            'leftTicketDTO.to_station': form.to_station_code,
            'purpose_codes': 'ADULT',
        }
        logger.info(f'fetch trains params: {_params}')
        cookies = await (await get_cookie_store()).get_valid_cookie()
        _headers = HeadersBuilder() \
            .add_header('Referer', 'https://kyfw.12306.cn/otn/leftTicket/init?') \
            .add_header('Cookie', cookies) \
            .add_header('if-modified-since', '0').build()
        async with get_async_client() as client:
            response = await client.get(_url, params=_params, headers=_headers, cookies=None)
            if response.status_code != 200:
                logger.warning(f"fetch trains error: response: {response.status_code} {response.text}")
                raise Exception('fetch_trains ERROR')
            _raw_data = response.json()
            _x = _raw_data['data']
            _result = await parse_ticket_data(_x, dep_date=form.dep_date.strftime('%Y-%m-%d'))
        return _result


async def fetch_train_schedule(form):
    semaphore = await get_semaphore('fetch_train_schedule')
    async with semaphore:
        _url = get_url('QUERY_TRAIN_SCHEDULE')
        _params = {
            'leftTicketDTO.train_no': form.train_no,
            'leftTicketDTO.train_date': form.train_date.strftime('%Y-%m-%d'),
            'rand_code': ''
        }
        logger.info(f'params: {_params}')
        _headers = HeadersBuilder() \
            .add_header('Cookie', await (await get_cookie_store()).get_valid_cookie()) \
            .add_header('Referer', 'https://kyfw.12306.cn/otn/queryTrainInfo/init').build()
        async with get_async_client() as client:
            response = await client.get(_url, params=_params, headers=_headers)
            response.raise_for_status()
        raw_data = response.json()
        stop_info_list = raw_data.get('data', {}).get('data')
        raw_dict = {
            'train_no': form.train_no,
            'train_date': form.train_date.strftime('%Y-%m-%d'),
            'stop_info_list': parse_stop_info_list(stop_info_list)
        }
        return TrainSchedule.from_raw_dict(raw_dict)


async def fetch_train_no(train_code: str, train_date: str = (datetime.now()).strftime("%Y%m%d"), **kwargs):
    semaphore = await get_semaphore('fetch_train_no')
    async with semaphore:
        train_date = train_date.replace("-", "")
        _url = get_url('QUERY_TRAIN_NO')
        _params = {
            'keyword': train_code,
            'date': train_date
        }
        _headers = HeadersBuilder() \
            .add_header('Cookie', await (await get_cookie_store()).get_valid_cookie()) \
            .add_header('Referer', 'https://kyfw.12306.cn/').build()
        async with get_async_client() as client:
            response = await client.get(_url, params=_params, headers=_headers)
            if response.status_code != 200:
                return None
            _raw_data = response.json()
            _result = _raw_data.get('data')
            train_no_model_list = [MTrainNo.to_train_no(x) for x in _result]
            return train_no_model_list


async def fetch_all_stations() -> List[Station]:
    logger.info('fetch_all_stations')
    _headers = HeadersBuilder().build()
    async with get_async_client() as client:
        response = await client.get('https://www.12306.cn/index/', headers=_headers)
        response.raise_for_status()
        tree = html.fromstring(response.text)
        station_name_js_src = tree.xpath("//script[contains(@src, './script/core/common/station_name_')]/@src")[
            0].strip('.')
        if station_name_js_src:
            station_name_js_url = urllib.parse.urljoin('https://www.12306.cn/', f'index{station_name_js_src}')
            response = await client.get(station_name_js_url, headers=_headers)
            response.raise_for_status()
            text: str = response.text.strip("var station_names =").strip("';")
            station_names = text.split("|||")
            if station_names[-1] == '':
                station_names = station_names[:-1]
            stations = []
            for station_name in station_names:
                parts = station_name.strip("@").split('|')
                if len(parts) < 8:
                    logger.warning(f"解析车站失败:{station_name}")
                    continue
                try:
                    station = Station(name=parts[1], pinyin_abbr=parts[0], pinyin=parts[3], code=parts[2],
                                      city=parts[7])

                except Exception as e:
                    logger.warning(f'解析车站失败: {station_name} err:{exception_utils.extract_exception_traceback(e)}')
                    continue
                stations.append(station)
            return stations
        raise Exception("获取所有车站失败, 解析最新车站js失败")
