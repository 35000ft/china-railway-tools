from fastapi import APIRouter

from app.schemas.response import Response
from china_railway_tools.api.train import *
from china_railway_tools.schemas.query import QueryTrains
from china_railway_tools.schemas.train import TrainInfo

router = APIRouter()


def get_router():
    return router


@router.post("/query/tickets")
async def _query_tickets(form: QueryTrains) -> Response[List[TrainInfo]]:
    return Response.success(await query_tickets(form))


@router.post("/query/train-prices")
async def _query_train_prices(form: QueryTrainTicket) -> Response[TrainTicketResponse]:
    return Response.success(await query_train_prices(form))


@router.post("/query/schedule")
async def _query_train_schedule(form: QueryTrainSchedule) -> Optional[TrainSchedule]:
    return Response.success(await query_train_schedule(form))
