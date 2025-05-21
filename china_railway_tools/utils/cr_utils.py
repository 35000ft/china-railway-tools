import logging
import re

from china_railway_tools.schemas.train import *
from china_railway_tools.utils.cr_decoder import decode_price, decode_ticket_data
from china_railway_tools.utils.exception_utils import extract_exception_traceback

logger = logging.getLogger(__name__)


def calc_stopover_time(dep_time: str, arr_time: str):
    """

    :param dep_time: like 23:30
    :param arr_time: like 23:23
    :return:
    """

    def to_minutes(time_str):
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes

    if dep_time == '----' or arr_time == '----':
        return 0
    arr_minutes = to_minutes(arr_time)
    dep_minutes = to_minutes(dep_time)

    if dep_minutes < arr_minutes:
        dep_minutes += 24 * 60
    diff = dep_minutes - arr_minutes
    return diff


def parse_stop_info_list(_data: dict):
    return [
        StopInfo(station_name=x.get('station_name'),
                 arr_time=x.get('arrive_time'),
                 dep_time=x.get('start_time'),
                 stopover_time=calc_stopover_time(x.get('start_time', '00:00'), x.get('arrive_time', '00:00')),
                 duration=x.get('running_time', '--'),
                 arr_day_diff=int(x.get('arrive_day_diff')),
                 station_train_code=x.get('station_train_code'))
        for x in _data]


def train_data_filter(_train_info: TrainInfo, train_no: str, from_station: str = None, to_station: str = None) -> bool:
    condition = True
    if from_station is not None:
        condition = condition and _train_info.from_station_code == from_station
    if to_station is not None:
        condition = condition and _train_info.to_station_code == to_station
    if train_no is not None:
        condition = condition and _train_info.train_no == train_no
    return condition


def filter_train_by_code(train_info_list: List[TrainInfo], train_code_patterns: List[str]) -> List[TrainInfo]:
    def convert_to_regex(pattern):
        # 初始化正则表达式字符串
        regex = ""

        # 遍历模式字符
        i = 0
        while i < len(pattern):
            char = pattern[i]
            if char == '_':
                # 第一个 "_" 是字母占位符
                if i == 0:
                    regex += "[A-Za-z0-9]"
                else:
                    regex += "[0-9]"
                i += 1
            elif char == '*':
                # "*" 表示任意字符，可以用 ".*"
                regex += "[0-9]*"
                break
            elif char.isdigit() or char.isalpha():
                # 如果是字母或数字，直接按原样匹配
                regex += f"{char}"
                i += 1
            else:
                # 其他字符按原样匹配
                regex += re.escape(char)
                i += 1

        # 如果没有 "_" 或 "*"，则表示完全匹配
        if not ('_' in pattern or '*' in pattern):
            regex = "^" + regex + "$"
        else:
            # 有 "_" 或 "*" 的时候，表示部分匹配，开始于开头并结束于结尾
            regex = "^" + regex + "$"
        return regex

    result_set = set()
    for train_code_pattern in train_code_patterns:
        _regex = convert_to_regex(train_code_pattern)
        if not _regex:
            continue
        # 使用 filter 来筛选并返回符合条件的元素
        matching_items = list(filter(lambda x: re.match(_regex, x.train_code), train_info_list))

        # 将匹配到的元素添加到 result_set
        result_set.update(matching_items)  # 使用 update 批量添加元素
    return list(result_set)


async def parse_ticket_data(_data: dict, dep_date: str) -> List[TrainInfo]:
    try:
        _result = decode_ticket_data(_data['result'], _data['map'])
        _result = [x.get('queryLeftNewDTO') for x in _result]
        train_info_list = []
        for item in _result:
            _seat_types = [str(key).strip('num').upper() for key, value in item.items() if
                           '_num' in key and value != '--']
            # _prices: [{'price': 214, 'seatType': '一等座'}]
            _prices = []
            for _seat in _seat_types:
                _p = decode_price(item['yp_info_new'], _seat)
                if not _p:
                    continue
                _p['stock'] = item.get(f'{_seat.lower()}num')
                _prices.append(_p)
            item['prices'] = _prices
            train_info = TrainInfo.from_raw_dict(dep_date, item, )
            train_info_list.append(train_info)
        return train_info_list
    except Exception as e:
        logger.error(extract_exception_traceback(e))
