import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(BASE_DIR, '..', 'data', 'gpu_1986-2026.csv')
OUTPUT_PATH = os.path.join(BASE_DIR, '..', 'data', 'gpu_info_cleaned.csv')

KEEP_COLUMNS = [
    'Brand',
    'Name',
    'Graphics Card__Release Date',
    'Graphics Processor__GPU Name',
    'Graphics Processor__Codename',
    'Render Config__Shading Units',
    'Clock Speeds__Boost Clock',
    'Memory__Memory Size',
    'Memory__Memory Type',
    'Memory__Memory Bus',
    'Memory__Bandwidth',
    'Theoretical Performance__FP32 (float)',
    'Board Design__TDP',
    'Graphics Card__Launch Price'
]