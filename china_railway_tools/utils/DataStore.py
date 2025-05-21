import threading
import time
from datetime import datetime, timedelta
from typing import List


def calc_node_weight(child: 'Node', now_time: datetime, alpha=-0.5, beta=0.5) -> float:
    """根据last_visit和total_visit计算节点的权重"""
    time_diff = (now_time - child.last_visit).total_seconds()
    return alpha * time_diff + beta * child.total_visit


class Node(object):
    def __init__(self, value, ttl_seconds: int = None, capacity: int = 100):
        now = datetime.now()
        self.children: dict | None = None
        self.expire: datetime | None = None if ttl_seconds is None else now + timedelta(seconds=ttl_seconds)
        self.last_visit: datetime = now
        self.total_visit: int = 1
        self.value = value
        # 子节点最大容量
        self.capacity: int = capacity

    def get(self, key: str, default=None):
        self.last_visit = datetime.now()
        self.total_visit += 1
        if self.children is None:
            return default
        return self.children.get(key, default)

    def visit(self, key):
        if self.children is None:
            return None
        return self.children.get(key)

    def get_self(self):
        self.total_visit += 1
        self.last_visit = datetime.now()
        return self.value

    def set(self, key: str, value, ttl_seconds: int = None):
        if self.children is None:
            self.children = {}

        self.clean_expire()
        _v = Node(value, ttl_seconds)
        if len(self.children) >= self.capacity:
            now = datetime.now()
            lru_key = min(self.children, key=lambda k: calc_node_weight(self.children[k], now))
            del self.children[lru_key]
        self.children[key] = _v

    def remove(self, key: str):
        if self.children is not None:
            del self.children[key]

    def items(self):
        if self.children is None:
            return [], []
        return self.children.items()

    def clean_expire(self):
        if self.children is None:
            return
        keys_to_delete = []
        for key, record in self.children.items():
            if record.expire is not None and record.expire <= datetime.now():
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self.children[key]

    def __contains__(self, item):
        if self.children is None:
            return False
        return item in self.children


class DataStore(object):
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """
        确保只创建一个实例（单例模式）
        """
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, clean_frequency: int = 10, **kwargs):
        if not hasattr(self, 'store'):
            self.store = {}
            self.clean_frequency = clean_frequency
            self._stop_event = threading.Event()
            self._start_clear_expired_thread()

    def set(self, value, key_path=None, ttl_seconds=None, **kwargs):
        """
        设置多级键值对，并指定TTL(生存时间)
        :param value: 值
        :param ttl_seconds: TTL（以秒为单位），可选。如果不设置，则不过期。
        :param key_path: 点号分隔的键路径，如 'key1.subkey1.subsubkey1'
        """
        key_prefix = kwargs.get('key_prefix')
        key_index = kwargs.get('key_index')
        if key_index is not None and key_prefix is not None:
            key_path = f'{key_path}.{key_index}'

        if key_path is None or len(key_path) == 0:
            raise Exception('Key can not be Empty. Please input key_path or key_prefix and key_index.')
        keys = key_path.split('.')
        first_key = keys[0]
        if first_key not in self.store:
            self.store[first_key] = Node(None, None)
        if len(keys) == 1:
            self.store[first_key].value = value
            return

        current_level: Node = self.store[first_key]
        for key in keys[1:-1]:
            if key not in current_level:
                current_level.set(key, Node(value=None, ttl_seconds=None))
            current_level = current_level.visit(key)
        current_level.set(keys[-1], value, ttl_seconds)

    def get(self, key: str):
        """
        获取多级键的值，如果已过期则返回None
        :param key: 点号分隔的键路径
        :return: 值或None
        """
        if key is None or len(key) == 0:
            raise Exception('Key can not be Empty. Please input key_path or key_prefix and key_index.')
        keys = key.split('.')
        first_key = keys[0]

        if first_key not in self.store:
            return None
        if len(keys) == 1:
            return self.store[first_key].value

        current_level: Node = self.store[first_key]
        if len(keys) == 1:
            return current_level.get_self()

        for key in keys[1:-1]:
            if key not in current_level:
                current_level.set(key, None, ttl_seconds=60)
                return None
            current_level = current_level.visit(key)

        last_key = keys[-1]
        if last_key in current_level:
            record: Node = current_level.get(last_key)
            if record is None:
                return None
            if record.expire is None or record.expire > datetime.now():
                return record.get_self()
            else:
                # delete expired key
                record.remove(last_key)
        return None

    def get_by_prefix(self, key_prefix: str) -> dict:
        keys = key_prefix.split('.')
        current_level = self.store

        for key in keys:
            if key not in current_level:
                return {}
            current_level = current_level.get(key)
            if current_level is None:
                return {}
        #  v: Node|Any
        return {k: v for k, v in current_level.items()}

    def batch_get(self, key_prefix: str, index_list: List[str | int], index_name: str = None) -> list:
        index_list = [str(x) for x in index_list]
        _collection = self.get_by_prefix(key_prefix)
        if _collection is None:
            return []
        if type(_collection) is not dict:
            raise Exception(f"Value of key_prefix:{key_prefix} is not a collection")
        _collection = {
            k: v.value
            for k, v in dict(_collection).items()
        }
        if index_name is None:
            return [_collection.get(k) for k in _collection.keys() if k in index_list]
        return [x for x in _collection.values() if str(x[index_name]) in index_list]

    async def batch_set(self, key_prefix: str, value_list: list, index_name: str = 'id', ttl_seconds: int = None):
        for v in value_list:
            _key = f'{key_prefix}.{v[index_name]}'
            self.set(v, _key, ttl_seconds)

    def delete(self, key_path: str):
        """
        删除多级键值对
        :param key_path: 点号分隔的键路径
        """
        keys = key_path.split('.')
        current_level = self.store

        for key in keys[:-1]:
            if key not in current_level:
                return
            current_level = current_level[key]

        if keys[-1] in current_level:
            del current_level[keys[-1]]

    def clear_expired(self):
        """
        清理所有过期的键值对
        """

        def recursive_clear(current_level):
            if type(current_level) is Node:
                current_level.clean_expire()
            keys_to_delete = []
            for key, record in current_level.items():
                if record.expire is not None and record.expire <= datetime.now():
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                if type(current_level) is dict:
                    del current_level[key]

        recursive_clear(self.store)

    def _start_clear_expired_thread(self):
        """
        启动后台线程，每隔10秒清理一次过期的键值对。
        """

        def clear_expired_periodically():
            while not self._stop_event.is_set():
                self.clear_expired()
                time.sleep(self.clean_frequency)

        self.clear_expired_thread = threading.Thread(target=clear_expired_periodically, daemon=True)
        self.clear_expired_thread.start()

    def __repr__(self):
        return f"DataStore(total top keys:{len(self.store.keys())})"
