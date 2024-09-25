import logging
from data_reader.interface.grpc import client
from data_reader.endpoints.ros2 import core as ros2_core

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

mapping = {
    'ros2': ros2_core.main,
}

params = {
    "mode": "ros2",
    "topics": '/sensor_raw/rgbmatrix_02/image_raw',
    "msg_type": "image",
}

def main(mode="ros2"):
    assert mode in mapping.keys(), f"mode is not supported: {mode}"
    print(f"Readind Data from {mode} ...")
    
    module = mapping.get(mode)
    if module:
        module(
            params=params,
            callback=client.run
            )
    

if __name__ == "__main__":
    main(mode=params['mode'])