import uvicorn
from uuid import uuid4
from typing import Optional, Any
from fastapi import FastAPI, Depends, APIRouter
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException, Body, status, Request
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from asgi_correlation_id import correlation_id

from events_api.config import celery_utils
from events_api.routers.rt_video import generate_rt_video
from events_api.routers.video import generate_video
from events_api.routers.image import generate_image


def create_app() -> FastAPI:
    tags_metadata = [
        {
            "name": "Media Service Service Routing API",
            "description": "media service asynchronious processing with celery and RabbitMQ Broker"
        }
    ]

    app = FastAPI(
        openapi_tags=tags_metadata,
        debug=True,
        title="Media manager Asynchronous tasks processing with Celery and RabbitMQ",
        summary="",
        version="0.0.1",
        contact={
            "name": "Tannous Geagea",
            "url": "https://wasteant.com",
            "email": "tannous.geagea@wasteant.com",
        },
        openapi_url="/openapi.json",
    )

    origins = [
        "http://localhost:8080",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["X-Requested-With", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )


    app.celery_app = celery_utils.create_celery()
    app.include_router(generate_rt_video.router)
    app.include_router(generate_video.router)
    app.include_router(generate_image.router)
    
    return app

app = create_app()
celery = app.celery_app

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    description = exc.args[0]
    return await http_exception_handler(
        request,
        HTTPException(
            500,
            {"code": "generic_exception", "message": description},
            headers={"X-Request-ID": correlation_id.get() or ""},
        ),
    )
    
    
if __name__ == "__main__":

    uvicorn.run("main:app", host="0.0.0.0", port=18042, log_level="debug", reload=True)