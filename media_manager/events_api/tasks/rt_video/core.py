import os
import django
django.setup()

import json
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

from common_utils.media.edge_to_cloud import sync
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
    
    # if event_model.status ==  'completed':
    #     data = {
    #         "action": "ignored",
    #         "time": datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
    #         "results": f"ignore request - event_id {event.event_id} already processed and executed"
    #     }
    #     return data
    
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
                media_type="video",
                source_id=source,
                )
            
            video_path = get_media_path(media_model, filename=filename)
            if not os.path.exists(
                os.path.dirname(f"{settings.MEDIA_ROOT}/{video_path}")
            ):
                os.makedirs(os.path.dirname(f"{settings.MEDIA_ROOT}/{video_path}"))
            
            media_model.media_file = video_path
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
                
                _data = {
                    "delivery_id": event.event_id,
                    "media_id": media_model.media_id,
                    "media_name": media_model.media_name,
                    "media_type": media_model.media_type,
                    "media_url": media_model.media_file.url,
                        }
                
                params = {
                    'event_id': media_model.media_id,
                    'source_id': "media-manager",
                    'blob_name': os.path.basename(media_model.media_file.url),
                    'container_name': "delivery",
                    'target': "delivery/media",
                    'data': json.dumps(_data),
                }
                
                sync(
                    url=f"http://{os.getenv('EDGE_CLOUD_SYNC_HOST', '0.0.0.0')}:{os.getenv('EDGE_CLOUD_SYNC_PORT', '27092')}/api/v1/event/media",
                    media_file=f"{video_paths[source]}",
                    params={   
                        'event_id': media_model.media_id,
                        'source_id': "media-manager",
                        'blob_name': os.path.basename(media_model.media_file.url),
                        'container_name': "delivery",
                        'target': "delivery/media",
                        'data': json.dumps(
                            {
                                "delivery_id": event.event_id,
                                "media_id": media_model.media_id,
                                "media_name": media_model.media_name,
                                "media_type": media_model.media_type,
                                "media_url": media_model.media_file.url,    
                            }
                        )
                    },
                )
            
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