import os
import grpc
import json
import sys
import uuid
import time
import logging
from data_reader.interface.grpc import data_acquisition_pb2
from data_reader.interface.grpc import data_acquisition_pb2_grpc
from common_utils.services.redis_manager import RedisManager


redis_manager = RedisManager(
    host=os.environ['REDIS_HOST'],
    port=os.environ['REDIS_PORT'],
    db=os.environ['REDIS_DB'],
    password=os.environ['REDIS_PASSWORD'],
)

def run(payload):
    try:
        with grpc.insecure_channel(f'localhost:{os.environ.get("GRPC_DATA_READER")}') as channel:
            start_time = time.time()
            stub = data_acquisition_pb2_grpc.ComputingUnitStub(channel)
            
            assert isinstance(payload, dict), f"payload are expected to be dict, but got {type(payload)}"
            assert 'cv_image' in payload.keys(), f"key: cv_image not found in payload"
            assert 'img_key' in payload.keys(), f"key: img_key not found in payload"
            assert 'set_name' in payload.keys(), f"key: set_name not found in payload"
            
            if not(len(payload)):
                return
            
            cv_image = payload["cv_image"]
            img_key = payload["img_key"]
            set_name = payload["set_name"]
            
            status, img_key = redis_manager.handle_storage_by_timestamp(
                image=cv_image,
                key=img_key,
                expire=int(os.getenv('REDIS_EXPIRE', 60)),
                set_name=set_name,
            )
            
            if not status:
                logging.warning('Failed to handle storage with Redis')
                return
            
            
            signal = {key: value for key, value in payload.items() if key!='cv_image'}
            memory_info = {
                'used_memory_human': redis_manager.memory_info['used_memory_human'],
                'used_memory_peak_human': redis_manager.memory_info['used_memory_peak_human'],
            }
            
            signal = {
                **signal,
                **memory_info,
            }
            
            data = json.dumps(signal)
            response = stub.ProcessData(data_acquisition_pb2.ProcessDataRequest(data=data))
            response_data = json.loads(response.result)
                        
            exectution_time = time.time() - start_time

            print(f"Execution Time: {int(exectution_time * 1000)} milliseconds!")
            print("Impurity Computing Service responded with updated data:", response_data)
            
    except Exception as err:
        logging.error(f"Error while reading and processing data in data acquisition: {err}")