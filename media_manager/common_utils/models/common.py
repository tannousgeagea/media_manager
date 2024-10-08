
import django
django.setup()
import logging
from datetime import datetime, timezone

from database.models import (
    EdgeBoxInfo, 
    Event, 
    Media,
)


DATETIME_FORMAT = "%Y-%m-%d %H-%M-%S"

def get_event(event):
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
    event_model.timestamp = event.timestamp.replace(tzinfo=timezone.utc)
    event_model.save()
    
    return event_model


def get_media(
    event: Event, 
    media_id:str, 
    media_name:str,
    media_type:str,
    source_id:str=None,
    meta_info:dict=None,
    
    ):
    
    success = False
    media = None
    try:

        media = Media()
        media.event=event
        media.media_id=media_id
        media.media_name=media_name
        media.media_type=media_type
        media.source_id = source_id
        media.meta_info=meta_info
        success = True
    except Exception as err:
        logging.error(f"Error while save media file: {err}")
        
    return success, media