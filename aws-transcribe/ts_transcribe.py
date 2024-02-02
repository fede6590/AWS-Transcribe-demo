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
download_lock = asyncio.Lock()


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

bucket_name = os.environ.get('BUCKET', 'poc-subtitulos')
# prefix = os.environ.get('PREFIX', 'live')
region = 'us-east-1'
temp = 'temp'


class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                logger.info(alt.transcript)


def create_transcribe_client(region):
    try:
        session = boto3.Session(region_name=region)
        _ = session.client('transcribe')  # Test for IAM role availability
        return TranscribeStreamingClient(region=region)
    except Exception as e:
        logger.error(f'Error: {e}')
        raise e


async def download_ts_files(bucket_name, folder):
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    loop = asyncio.get_event_loop()

    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page['Contents']:
            if obj['Key'].endswith('.ts'):
                async with download_lock:
                    try:
                        await loop.run_in_executor(
                            None,
                            s3.download_file,
                            bucket_name,
                            obj['Key'],
                            os.path.join(
                                folder,
                                os.path.basename(obj['Key'])
                                )
                        )
                        logger.info(f"Downloaded file: {obj['Key']}")
                    except FileNotFoundError:
                        logger.error(f"File not found: {obj['Key']}")
    cleanup_oldest_file(50, folder)  # Keep only the X most recent files


async def ts_stream(folder):
    while True:
        # Get the list of .ts files in the directory
        ts_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.ts')]
        if not ts_files:
            continue

        # Sort the files by modification time and take the latest one
        latest_file = sorted(ts_files, key=lambda f: os.path.getmtime(f), reverse=True)[0]

        # Use ffmpeg to extract audio from the .ts file
        cmd = ['ffmpeg', '-i', latest_file, '-vn', '-acodec', 'pcm_s16le', '-f', 'wav', '-']
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        stdout, _ = await proc.communicate()

        yield stdout


async def write_chunks(stream, folder):
    async for stdout in ts_stream(folder):
        await stream.input_stream.send_audio_event(audio_chunk=stdout)
    await stream.input_stream.end_stream()


def cleanup_oldest_file(max_files, folder):
    ts_files = glob.glob(os.path.join(folder, '*.ts'))

    # If there are more than max_files, delete the oldest ones
    if len(ts_files) > max_files:
        ts_files.sort(key=os.path.getctime)
        for file in ts_files[:len(ts_files) - max_files]:
            os.remove(file)


async def basic_transcribe(bucket_name, region, folder):
    client = create_transcribe_client(region)

    # Start transcription to generate our async stream
    stream = await client.start_stream_transcription(
        language_code="en-US",
        media_sample_rate_hz=16000,
        media_encoding="pcm"
    )

    # Instantiate our handler and start processing events
    handler = MyEventHandler(stream.output_stream)
    await download_ts_files(bucket_name, folder)
    await asyncio.gather(write_chunks(stream, folder), handler.handle_events())


if __name__ == "__main__":
    asyncio.run(basic_transcribe(bucket_name, region, temp))
