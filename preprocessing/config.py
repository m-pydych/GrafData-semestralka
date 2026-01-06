import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_CSV_PATH = os.path.join(BASE_DIR, '..', 'data', 'gpu_1986-2026.csv')
PROCESSED_CSV_PATH = os.path.join(BASE_DIR, '..', 'data', 'gpu_info_cleaned.csv')
OUTPUT_RDF_PATH = os.path.join(BASE_DIR, '..', 'data', 'gpu_data.ttl')

KEEP_COLUMNS = [
    'Brand',
    'Name',
    'Graphics Card__Release Date',
    'Graphics Processor__GPU Name',
    'Graphics Processor__Codename',
    'Graphics Processor__Architecture',
    'Render Config__Shading Units',
    'Clock Speeds__Base Clock',
    'Clock Speeds__Boost Clock',
    'Memory__Memory Size',
    'Memory__Memory Type',
    'Memory__Memory Bus',
    'Memory__Bandwidth',
    'Theoretical Performance__FP32 (float)',
    'Board Design__TDP',
    'Graphics Card__Launch Price'
]

RENAME_COLUMNS = {
    'Brand': 'brand',
    'Name': 'product_name',
    'Graphics Card__Release Date': 'release_date',
    'Graphics Processor__GPU Name': 'gpu_name',
    'Graphics Processor__Codename': 'gpu_codename',
    'Graphics Processor__Architecture': 'architecture',
    'Render Config__Shading Units': 'shading_units',
    'Clock Speeds__Base Clock': 'base_clock',
    'Clock Speeds__Boost Clock': 'boost_clock',
    'Memory__Memory Size': 'mem_size',
    'Memory__Memory Type': 'mem_type',
    'Memory__Memory Bus': 'mem_bus',
    'Memory__Bandwidth': 'bandwidth',
    'Theoretical Performance__FP32 (float)': 'tflops_fp32',
    'Board Design__TDP': 'tdp',
    'Graphics Card__Launch Price': 'launch_price'
}

MONTH_MAP = {
    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
    'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
}