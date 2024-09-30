import os
import cv2
import uuid
import django
django.setup()

import time
import logging
import numpy as np
from celery import Celery
from celery import shared_task
from datetime import datetime, timedelta
from common_utils.services.redis_manager import RedisManager
from common_utils.media.video_utils import generate_video as gen_video
from common_utils.media.video_utils import get_video_length
from common_utils.models.common import get_event, get_media
from django.conf import settings
from database.models import (
    get_media_path,
)

FRAME_RATE = int(os.environ.get('FRAME_RATE', 5))
redis_manager = RedisManager(
    host=os.environ.get('REDIS_HOST'),
    port=os.environ.get('REDIS_PORT'),
    password=os.environ.get('REDIS_PASSWORD'),
    db=os.environ.get("REDIS_DB"),
)

@shared_task(bind=True,autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5}, ignore_result=True,
             name='video:generate_video')
def generate_video(self, event, **kwargs):
    data:dict = {}
    try:
        set_name = "/sensor_raw/rgbmatrix_02/image_raw"
        event_model = get_event(event)
        timestamp = time.time()
        images = redis_manager.redis_client.zrangebyscore(set_name, min=(timestamp - 120), max=timestamp + 10)
        
        if not images:
            event_model.status = "failed"
            event_model.status_description = f"No images found in {set_name}"
            event_model.save()
            raise ValueError(f'No images found in {set_name}')
        
        frames = []
        for image in images:
            frames.append(
                cv2.imdecode(
                    np.frombuffer(image, dtype=np.uint8), 
                    cv2.IMREAD_COLOR)
            )
            
            
        filename = f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.mp4'
        media = get_media(event, media_id=str(uuid.uuid4()), media_name="video", media_type="video")
        video_path = get_media_path(media, filename=filename)

        if not os.path.exists(
            os.path.dirname(f"{settings.MEDIA_ROOT}/{video_path}")
        ):
            os.makedirs(os.path.dirname(f"{settings.MEDIA_ROOT}/{video_path}"))        

        gen_video(
            frames=frames,
            framerate=FRAME_RATE,
            video_path=f"{settings.MEDIA_ROOT}/{video_path}",
            scale=0.5,
        )

        if not os.path.exists(f"{settings.MEDIA_ROOT}/{video_path}"):
            event_model.status = "failed"
            event_model.status_description = f"{settings.MEDIA_ROOT}/{video_path} not found"
            event_model.save()
            
            
        media.file_size = os.stat(f"{settings.MEDIA_ROOT}/{video_path}").st_size
        h, m, s = get_video_length(path=f"{settings.MEDIA_ROOT}/{video_path}")
        media.duration = timedelta(hours=h, minutes=m, seconds=s) 
        media.save()        

        data = {
            "action": "done",
            "time": datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        }
        
        event_model.status = "completed"
        event_model.save()
        return data
            
    except Exception as err:
        raise ValueError(f"Error generating video: {err}")