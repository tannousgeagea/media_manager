import os
import django
django.setup()

from celery import Celery
from celery import shared_task
from datetime import datetime, timedelta
from common_utils.media.image_retrieval import ImageRetriever
from common_utils.media.video_utils import get_video_length
from common_utils.models.common import get_event, get_media
from django.conf import settings
from database.models import (
    get_media_path,
)

FRAME_RATE = int(os.environ.get('FRAME_RATE', 5))
image_retriever = ImageRetriever()

@shared_task(bind=True,autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5}, ignore_result=True,
             name='start_rt_video:start_retrieving')
def start_retrieving(self, event, **kwargs):
    data: dict = {}
    event_model = get_event(event)
    if event_model.status == "active":
        data = {
            "action": "ignored",
            "time": datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
            "results": "ignore request - start event already in progress"
        }
        
        event_model.status_description = f'{datetime.now().strftime("%Y-%m-%d %H-%M-%S")}: ignore request - start event already in progress'
        event_model.save()
        return data
    
    topics = event.topics.split(",")
    if isinstance(event.topics, str):
        event.topics = [event.topics]
    
    for source in topics:
        image_retriever.start(
            set_name=source,
            )
    
    data.update(
        {
            "action": "started",
            "time": datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
        }
    )
    
    event_model.status = "active"
    event_model.save()
    
    return data

@shared_task(bind=True,autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5}, ignore_result=True,
             name='stop_rt_video:stop_retrieving')
def stop_retrieving(self, event, **kwargs):
    try:
        event_model = get_event(event)
        if not event_model.status == "active":
            data = {
                "action": "ignored",
                "time": datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
                "results": "ignore request - start event has to come first"
            }
            
            event_model.status = "failed"
            event_model.status_description = f'{datetime.now().strftime("%Y-%m-%d %H-%M-%S")}: ignore request - start event has to come first'
            event_model.save()
            
            return data
        
        topics = event.topics.split(",")
        if isinstance(event.topics, str):
            event.topics = [event.topics]
        
        media = {}
        video_paths = {}
        for source in topics:
            filename = f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.mp4'
            success, media_model = get_media(
                event=event_model, 
                media_id=event.event_id, 
                media_name=event.event_name, 
                media_type="video"
                )
            
            video_path = get_media_path(media_model, filename=filename)
            if not os.path.exists(
                os.path.dirname(f"{settings.MEDIA_ROOT}/{video_path}")
            ):
                os.makedirs(os.path.dirname(f"{settings.MEDIA_ROOT}/{video_path}"))
            
            media_model.media_file = video_path
            media_model.source_id = source
            media[source] = media_model
            video_paths[source] = f"{settings.MEDIA_ROOT}/{video_path}"
            
        image_retriever.stop(
            video_paths=video_paths
        )
        
        for source, media_model in media.items():
            if os.path.exists(video_paths[source]):
                media_model.file_size = os.stat(video_paths[source]).st_size
                h, m, s = get_video_length(path=video_paths[source])
                media_model.duration = timedelta(hours=h, minutes=m, seconds=s) 
                media_model.save()
            
        data = {
            "action": "stopped",
            "time": datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        }
        
        event_model.status = "completed"
        event_model.save()
        return data
        
    except Exception as err:
        event_model.status = "failed"
        event_model.status_description  = f"Error: {err}"
        event_model.save()
        
        image_retriever.stop()
        raise ValueError(f"Error: {err}")
