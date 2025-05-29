from typing import List

from fastapi import APIRouter, Query

from app.schemas.response import Response
from app.util.fastapi_utils import cache_control
from china_railway_tools.api.station import query_station
from china_railway_tools.schemas.station import Station

router = APIRouter()


def get_router():
    return router


@router.get('/query/keyword', response_model=List[Station])
@cache_control(max_age=86400)
async def _query_station(keyword: str = Query(None, title='车站名/拼音缩写/城市名', example='广州')):
    return Response.gen_response(await query_station(keyword))
