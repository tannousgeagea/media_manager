import re
import cv2
import pytz
import logging
import subprocess
from PIL import Image
from decimal import Decimal
from datetime import datetime, timedelta
from common_utils.models.common import get_timezone, convert_to_local_time

def create_video_from_frames(output_filename, width, height, framerate=24):
    command = [
        'ffmpeg',
        '-y',  # Overwrite output file if it exists
        '-f', 'rawvideo',  # Input format
        '-vcodec', 'rawvideo',
        '-s', f'{width}x{height}',  # Size of one frame
        '-pix_fmt', 'rgb24',
        '-r', str(framerate),  # Framerate
        '-i', '-',  # The input comes from a pipe
        '-an',  # No audio
        '-vcodec', 'libx264',  # Use H.264 codec
        '-preset', 'slow',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
        # '-b:v', '7000k',  # Bitrate
        '-movflags', '+faststart',  # Fast start for MP4 files
        output_filename
    ]

    # Open the FFmpeg process
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    return process

def convert_bgr_to_rgb(opencv_image):
    return cv2.cvtColor(opencv_image, cv2.COLOR_BGR2RGB)

def generate_video(frames, timestamps, framerate, video_path, location=None, scale=1.):
    success = False
    if not frames:
        print('No data are found')
        return success
    
    tz = pytz.timezone(get_timezone())
    h0, w0, _ = frames[0].shape
    h, w = int(h0 * scale), int(w0 * scale)
    process = create_video_from_frames(video_path, width=w, height=h, framerate=framerate)
    _location = f" | {location}" if location else '' 
    for i, frame in enumerate(frames):
        frame = cv2.resize(frame, (w, h), interpolation=cv2.INTER_NEAREST)
        timestamp = convert_to_local_time(dt=datetime.fromtimestamp(float(timestamps[i])), tenant_tz=tz, format='%Y-%m-%d %H:%M:%S') + _location
        cv2.putText(frame, timestamp, (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        image = Image.fromarray(convert_bgr_to_rgb(frame))
        process.stdin.write(image.tobytes())

    process.stdin.close()
    process.wait()
    

def get_video_length(path):
    process = subprocess.Popen(['/usr/bin/ffmpeg', '-i', path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = process.communicate()
    # Correcting the regex pattern
    matches = re.search(r"Duration:\s(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d+\.\d+)", stdout.decode('utf-8'), re.DOTALL).groupdict()

    hours = float(matches['hours'])
    minutes = float(matches['minutes'])
    seconds =float(matches['seconds'])

    return hours, minutes, seconds
