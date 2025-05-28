from typing import List

from fastapi import APIRouter, Query

from app.schemas.response import Response
from china_railway_tools.api.station import query_station
from china_railway_tools.schemas.station import Station

router = APIRouter()


def get_router():
    return router


@router.get('/query/keyword')
async def _query_station(keyword: str = Query(None, title='车站名/拼音缩写/城市名', example='广州')) \
        -> Response[List[Station]]:
    return Response.success(await query_station(keyword))
