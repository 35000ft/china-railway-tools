from fastapi import APIRouter

from app.schemas.response import Response
from app.util.fastapi_utils import cache_control
from china_railway_tools.api.train import *
from china_railway_tools.schemas.query import QueryTrains
from china_railway_tools.schemas.train import TrainInfo

router = APIRouter()


def get_router():
    return router


@router.post("/query/tickets", response_model=List[TrainInfo])
async def _query_tickets(form: QueryTrains):
    return Response.gen_response(await query_tickets(form))


@router.post("/query/train-prices", response_model=TrainTicketResponse)
async def _query_train_prices(form: QueryTrainTicket):
    return Response.gen_response(await query_train_prices(form))


@router.post("/query/schedule", response_model=TrainSchedule)
@cache_control(max_age=7200)
async def _query_train_schedule(form: QueryTrainSchedule):
    return Response.gen_response(await query_train_schedule(form))
