import json
import time
import uuid
from pathlib import Path
from fastapi import Request
from datetime import datetime
from pydantic import BaseModel
from fastapi.routing import APIRoute
from typing_extensions import Annotated
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, APIRouter, Request, Header, Response
from typing import Callable, Union, Any, Dict, AnyStr, Optional, List
from events_api.tasks.image import core


class TimedRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            before = time.time()
            response: Response = await original_route_handler(request)
            duration = time.time() - before
            response.headers["X-Response-Time"] = str(duration)
            print(f"route duration: {duration}")
            print(f"route response: {response}")
            print(f"route response headers: {response.headers}")
            return response

        return custom_route_handler


class ApiResponse(BaseModel):
    status: str
    task_id: str
    data: Optional[Dict[AnyStr, Any]] = None


class ApiRequest(BaseModel):
    gate_id:str
    event_id:str
    event_name:str
    event_type:str
    timestamp: datetime
    event_description:str
    topic:str


router = APIRouter(
    prefix="/api/v1",
    tags=["Images"],
    route_class=TimedRoute,
    responses={404: {"description": "Not found"}},
)


@router.api_route(
    "/event/image", methods=["POST"], tags=["Images"]
)
async def generate_image(
    response:Response,
    event:ApiRequest = Depends(),
    x_request_id: Annotated[Optional[str], Header()] = None,
) -> dict:

    task = core.generate_image.apply_async(args=(event,), task_id=x_request_id)
    result = {"status": "received", "task_id": task.id, "data": {}}

    return result