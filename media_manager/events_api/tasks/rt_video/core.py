import os
import django
from celery import Celery
from celery import shared_task
from datetime import datetime
from common_utils.media.image_retrieval import ImageRetriever


FRAME_RATE = int(os.environ.get('FRAME_RATE', 5))
image_retriever = ImageRetriever()

@shared_task(bind=True,autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5}, ignore_result=True,
             name='start_rt_video:start_retrieving')
def start_retrieving(self, **kwargs):
    data: dict = {}
    event = kwargs
    
    if image_retriever.retrieving_event.is_set():
        data = {
            "action": "ignored",
            "time": datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
            "results": "ignore request - start event already in progress"
        }
        return data
    
    image_retriever.start(
        set_name="/sensor_raw/rgbmatrix_02/image_raw",
        min_ts=event.get('timestamp'))
    data.update(
        {
            "action": "started",
            "time": datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
        }
    )
    
    return data

@shared_task(bind=True,autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5}, ignore_result=True,
             name='stop_rt_video:stop_retrieving')
def stop_retrieving(self, **kwargs):
    
    if not image_retriever.retrieving_event.is_set():
        data = {
            "action": "ignored",
            "time": datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
            "results": "ignore request - start event has to come first"
        }
        return data
    
    image_retriever.stop()
    data = {
        "action": "stopped",
        "time": datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    }
    return data


