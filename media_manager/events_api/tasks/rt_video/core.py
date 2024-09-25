import os
import django
django.setup()

from celery import Celery
from celery import shared_task
from datetime import datetime
from common_utils.media.image_retrieval import ImageRetriever

from database.models import (
    PlantInfo,
    EdgeBoxInfo,
    Event,
    Media,
)


FRAME_RATE = int(os.environ.get('FRAME_RATE', 5))
image_retriever = ImageRetriever()

@shared_task(bind=True,autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5}, ignore_result=True,
             name='start_rt_video:start_retrieving')
def start_retrieving(self, event, **kwargs):
    data: dict = {}
    
    if not EdgeBoxInfo.objects.filter(location=event.gate_id).exists():
        data = {
            "action": "ignored",
            "time": datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
            "results": f"gate id {event.gate_id} not found or not registered yet"
        }
        
        return data
    
    edge_box = EdgeBoxInfo.objects.get(location=event.gate_id)
    if Event.objects.filter(edge_box=edge_box, event_id=event.event_id).exists():
        event_model = Event.objects.get(edge_box=edge_box, event_id=event.event_id)
    else:
        event_model = Event()
    
    event_model.edge_box = edge_box
    event_model.event_id = event.event_id
    event_model.event_name = event.event_name
    event_model.event_type = event.event_type
    event_model.event_description =  event.event_description
    event_model.timestamp = event.timestamp
    
    if event_model.status == "active":
        data = {
            "action": "ignored",
            "time": datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
            "results": "ignore request - start event already in progress"
        }
        
        event_model.status_description = f'{datetime.now().strftime("%Y-%m-%d %H-%M-%S")}: ignore request - start event already in progress'
        event_model.save()
        return data
    
    image_retriever.start(
        set_name="/sensor_raw/rgbmatrix_02/image_raw",
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
    
    if not EdgeBoxInfo.objects.filter(location=event.gate_id).exists():
        data = {
            "action": "ignored",
            "time": datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
            "results": f"gate id {event.gate_id} not found or not registered yet"
        }
        
        return data
    
    edge_box = EdgeBoxInfo.objects.get(location=event.gate_id)
    if Event.objects.filter(edge_box=edge_box, event_id=event.event_id).exists():
        event_model = Event.objects.get(edge_box=edge_box, event_id=event.event_id)
    else:
        event_model = Event()
    
    event_model.edge_box = edge_box
    event_model.event_id = event.event_id
    event_model.event_name = event.event_name
    event_model.event_type = event.event_type
    event_model.event_description =  event.event_description
    event_model.timestamp = event.timestamp
    
    if not image_retriever.retrieving_event.is_set():
        data = {
            "action": "ignored",
            "time": datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
            "results": "ignore request - start event has to come first"
        }
        
        event_model.status = "failed"
        event_model.status_description = f'{datetime.now().strftime("%Y-%m-%d %H-%M-%S")}: ignore request - start event has to come first'
        event_model.save()
        
        return data
    
    image_retriever.stop()
    data = {
        "action": "stopped",
        "time": datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    }
    
    event_model.status = "completed"
    event_model.save()
    
    return data


