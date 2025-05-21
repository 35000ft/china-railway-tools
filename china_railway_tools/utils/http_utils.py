import logging
import traceback

import httpx
from httpx import Request, Response

from china_railway_tools.utils.exception_utils import extract_traceback

logger = logging.getLogger(__name__)


class HeadersBuilder:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/127.0.0.0 Safari/537.36',
        }

    def add_header(self, key, value):
        self.headers[key] = value
        return self

    def build(self):
        return self.headers


class LoggingEventHook:
    async def __call__(self, event, **kwargs):
        if type(event) is Request:
            request = event
            logger.debug(f"Fetching URL: {request.url}")
        elif type(event) is Response:
            response = event
            request = response.request
            if response.status_code != 200:
                logger.warning(f"Response Code: {response.status_code} for fetch URL: {request.url} "
                               f"Method: {request.method} {'Params:' + request.json() if request.method == 'POST' else ''} "
                               f"Called by: {extract_traceback(traceback.extract_stack())}")
            else:
                pass


def get_async_client():
    event_hook = LoggingEventHook()
    return httpx.AsyncClient(event_hooks={"request": [event_hook], "response": [event_hook]})
