import os
import time
import math
import django
from django.db import connection
from django.db.models import Q
from fastapi import status
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Callable
from fastapi import Request
from fastapi import Response
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.routing import APIRoute

django.setup()
from django.core.exceptions import ObjectDoesNotExist
from database.models import Event, Media


DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"

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
    

router = APIRouter(
    route_class=TimedRoute,
)


description = """
    TO DO
"""

@router.api_route(
    "/media/{event_id}", methods=["GET"], tags=["Media"], description=description
)
def get_data(response: Response, event_id:str):
    results:dict = {}
    try:
        
        if not Event.objects.filter(event_id=event_id).exists():
            results["error"] = {
                "status_code": "not found",
                "status_description": f"event id {event_id} not found",
                "detail": f"event id {event_id} not found",
            }
            
            response.status_code = status.HTTP_404_NOT_FOUND
            return results
        
        event = Event.objects.get(event_id=event_id)
        if event.status == "active":
            results = {
                "status_code": "in-progress",
                "status_description": f"event id {event_id} is still in progress",
                "detail": f"event id {event_id} is still in progress - try again later",
            }
            
            response.status_code = status.HTTP_202_ACCEPTED
            return results
        
        if event.status == "failed":
            results = {
                "status_code": "server error",
                "status_description": f"media generation failed for event id {event_id}",
                "detail": f"media generation failed for event id {event_id}: {event.status_description}",
            }
            
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return results
        
        result = []
        medias = Media.objects.filter(event=event)
        for media in medias:
            result.append(
                {
                    "name": media.media_name,
                    "url": media.media_file.url,
                    "timestamp": media.created_at.strftime(f"{DATE_FORMAT} {TIME_FORMAT}"),
                    "type": media.media_type,
                }
            )
        
        
        results['data'] = result
        results['status_code'] = "ok"
        results["detail"] = "data retrieved successfully"
        results["status_description"] = "OK"
        
        connection.close()
        
    except ObjectDoesNotExist as e:
        results['error'] = {
            'status_code': "non-matching-query",
            'status_description': f'Matching query was not found',
            'detail': f"matching query does not exist. {e}"
        }

        response.status_code = status.HTTP_404_NOT_FOUND
        
    except HTTPException as e:
        results['error'] = {
            "status_code": "not found",
            "status_description": "Request not Found",
            "detail": f"{e}",
        }
        
        response.status_code = status.HTTP_404_NOT_FOUND
    
    except Exception as e:
        results['error'] = {
            'status_code': 'server-error',
            "status_description": "Internal Server Error",
            "detail": str(e),
        }
        
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return results