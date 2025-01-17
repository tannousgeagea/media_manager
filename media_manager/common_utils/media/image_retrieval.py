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
        self.frames = {}
        self.image_ids = {}
        self.thread = None
        self.threads = {}
        
    def start(self, set_name:str, min_ts=None):
        self.retrieving_event.set()
        if set_name not in self.threads or not self.threads[set_name].is_alive():
            
            if min_ts is None:
                min_ts = time.time()
                
            thread = threading.Thread(target=self.retrieve_frames, args=(set_name, min_ts,))
            self.threads[set_name] = thread
            thread.start()

    def stop(self, video_paths:dict=None):
        self.retrieving_event.clear()
        
        for set_name, thread in self.threads.items():
            if thread.is_alive():
                thread.join()
            
            if video_paths:
                generate_video(
                    frames=self.frames[set_name],
                    timestamps=self.image_ids[set_name],
                    framerate=5,
                    video_path=video_paths[set_name],
                    scale=0.5
                )

    def retrieve_frames(self, set_name:str, min_ts=None):
        print('Start retrieving ...')
        if min_ts is None:
            min_ts = time.time()
        
        self.image_ids[set_name] = []
        self.frames[set_name] = []
        
        while self.retrieving_event.is_set():
            image_keys = redis_manager.redis_client.zrangebyscore(set_name, int(min_ts), '+inf', withscores=False)
            if not image_keys:
                logging.warning('Nothing to retrieve')
                continue
            
            for key in image_keys:
                if key in self.image_ids[set_name]:
                    continue
            
                success, image = redis_manager.retrieve_image(key=key)
                if not success:
                    continue
                
                print(f"Retrieving from {set_name}: {key} ... ...")
                self.image_ids[set_name].append(key)
                self.frames[set_name].append(image)
        
    
