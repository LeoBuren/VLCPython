import os

BASE_DIR = os.path.abspath(__file__)
BASE_FOLDER = os.path.dirname(
    BASE_DIR)
INPUT_FOLDER = os.path.join(BASE_FOLDER, 'input')
OUTPUT_FOLDER = os.path.join(BASE_FOLDER, 'output')
FFMPEG = 'ffmpeg -v 0 -loglevel error -stats -hide_banner'
OUTPUT_SETTINGS = '-ac 2 -c:v h264_nvenc -preset p6 -profile:v high -tune hq -rc-lookahead 8 -bf 2 -rc vbr -cq 26 -b:v 0 -maxrate 160M -bufsize 360M '
JOIN_AFTER = True
SCALE_FACTOR = 1.35
W = 1920
H = 1080
