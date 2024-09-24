import os
import cv2
import time
import logging
import threading
import numpy as np
from datetime import datetime
from .video_utils import generate_video
from common_utils.services.redis_manager import RedisManager

redis_manager = RedisManager(
    host=os.environ.get('REDIS_HOST'),
    port=os.environ.get('REDIS_PORT'),
    password=os.environ.get('REDIS_PASSWORD'),
    db=os.environ.get("REDIS_DB"),
)

class ImageRetriever:
    def __init__(self):
        self.retrieving_event = threading.Event()
        self.frames = []
        self.image_ids = []
        self.thread = None
        
    def start(self, set_name:str, min_ts=None):
        self.retrieving_event.set()
        if not self.thread or not self.thread.is_alive():
            
            if min_ts is None:
                min_ts = time.time()
                
            self.thread = threading.Thread(target=self.retrieve_frames, args=(set_name, min_ts,))
            self.thread.start()

    def stop(self):
        self.retrieving_event.clear()
        if self.thread:
            self.thread.join()
            self.thread = None
            
        generate_video(
            frames=self.frames,
            framerate=5,
            video_path='/home/appuser/src/test.mp4',
            scale=0.5
        )

    def retrieve_frames(self, set_name:str, min_ts=None):
        print('Start retrieving ...')
        if min_ts is None:
            min_ts = time.time()
            
        while self.retrieving_event.is_set():
            images = redis_manager.redis_client.zrangebyscore(set_name, int(min_ts), '+inf', withscores=True)
            if not images:
                logging.warning('Nothing to retrieve')
                continue
            
            for image, key in images:
                if key in self.image_ids:
                    continue
            
                image_array = np.frombuffer(image, dtype=np.uint8)
                image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                
                print(f"Retrieving: {key} ... ...")
                self.image_ids.append(key)
                self.frames.append(image)
        
    
