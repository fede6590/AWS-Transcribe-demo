import boto3
import subprocess


def read_next_file(bucket, prefix):
    s3_client = boto3.client('s3', region_name='us-east-1')

    latest_file = s3_client.get_paginator('list_objects_v2').paginate(Bucket=bucket, Prefix=prefix).max_keys(1).next_page()['Contents']
    if latest_file and latest_file[0]['Key'].endswith('.ts'):
        response = s3_client.get_object(Bucket=bucket, Key=latest_file[0]['Key'])
        return response['Body'].read()

    return None


def encoding(input_data):
    command = [
        'ffmpeg',
        '-i', 'pipe:0',  # Read input from stdin
        '-vn',        # Disable video
        '-acodec', 'pcm_s16le',  # Set audio codec to PCM 16-bit little-endian
        '-ar', '16000',  # Set audio sample rate to 16 kHz (not 44.1 kHz)
        '-ac', '1',     # Set audio channels to mono (not stereo)
        '-f', 'wav',    # Set output format to WAV
        '-'
    ]

    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        audio_data, error = process.communicate(input=input_data)
        return audio_data
    except Exception as e:
        raise RuntimeError(f"ERROR {e}")


def credentials_parser(credentials_path):
    with open(credentials_path, "r") as file:
        lines = file.readlines()

    aws_access_key_id = lines[1].split("=")[1].strip()
    aws_secret_access_key = lines[2].split("=")[1].strip()

    print("aws_access_key_id:", aws_access_key_id)
    print("aws_secret_access_key:", aws_secret_access_key)
    return aws_access_key_id, aws_secret_access_key
