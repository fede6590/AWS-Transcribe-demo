import asyncio
import nest_asyncio
import subprocess
import boto3
import os
import glob
import logging
import sys

from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

nest_asyncio.apply()


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

bucket_name = os.environ.get('BUCKET', 'poc-subtitulos')
prefix = os.environ.get('PREFIX', 'live')
region_name = 'us-east-1'


class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                logger.info(alt.transcript)


def create_transcribe_client():
    try:
        session = boto3.Session(region_name=region_name)
        _ = session.client('transcribe')  # Test for IAM role availability
        return TranscribeStreamingClient(region=region_name)
    except Exception as e:
        logger.error(f'Error: {e}')
        raise e


async def download_ts_files(bucket_name):
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    loop = asyncio.get_event_loop()

    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page['Contents']:
            if obj['Key'].endswith('.ts'):
                await loop.run_in_executor(
                    None,
                    s3.download_file,
                    bucket_name,
                    obj['Key'],
                    os.path.join('/temp/', obj['Key'])
                    )
                cleanup_oldest_file(10)  # Keep only the 10 most recent files


async def ts_stream():
    while True:
        # Get the list of .ts files in the directory
        ts_files = [os.path.join('/temp/', f) for f in os.listdir('/temp/') if f.endswith('.ts')]
        if not ts_files:
            continue

        # Sort the files by modification time and take the latest one
        latest_file = sorted(ts_files, key=lambda f: os.path.getmtime(f), reverse=True)[0]

        cmd = ['ffmpeg', '-i', latest_file, '-vn', '-acodec', 'pcm_s16le', '-f', 'wav', '-']
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        while True:
            chunk = await proc.stdout.read(1024 * 2)
            if not chunk:
                break
            yield chunk, None


async def write_chunks(stream):
    # This connects the raw audio chunks generator
    # and passes them along to the transcription stream.
    async for chunk, status in ts_stream():
        await stream.input_stream.send_audio_event(audio_chunk=chunk)
    await stream.input_stream.end_stream()


def cleanup_oldest_file(max_files):
    # Get a list of all .ts files in the '/temp/' directory
    ts_files = glob.glob(os.path.join('/temp/', '*.ts'))

    # If there are more than max_files, delete the oldest ones
    if len(ts_files) > max_files:
        ts_files.sort(key=os.path.getctime)
        for file in ts_files[:len(ts_files) - max_files]:
            os.remove(file)


async def basic_transcribe(bucket_name):
    client = create_transcribe_client()
    logger.info('CLIENT READY')
    # Start transcription to generate our async stream
    stream = await client.start_stream_transcription(
        language_code="en-US",
        media_sample_rate_hz=16000,
        media_encoding="pcm"
    )
    logger.info('STREAM READY')
    # Instantiate our handler and start processing events
    handler = MyEventHandler(stream.output_stream)
    logger.info('HANDLER READY')
    await download_ts_files(bucket_name)
    logger.info('FILES READY')
    await asyncio.gather(write_chunks(stream), handler.handle_events())
    logger.info('CHUNKS READY')
if __name__ == "__main__":
    asyncio.run(basic_transcribe(bucket_name))
    logger.info('RUN READY')
