import asyncio
import aiofile
import boto3
import os
import m3u8

from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
from amazon_transcribe.utils import apply_realtime_delay


SAMPLE_RATE = 16000
BYTES_PER_SAMPLE = 2
CHANNEL_NUMS = 1
REGION = "us-east-1"


class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                print(alt.transcript)


def get_ts_files_from_m3u8(m3u8_path):
    m3u8_obj = m3u8.load(m3u8_path)
    ts_files = [seg['uri'] for seg in m3u8_obj.segments]
    return ts_files


async def basic_transcribe():
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION
    )
    _ = session.client('transcribe')  # Test for IAM role availability
    client = TranscribeStreamingClient(region=REGION)

    stream = await client.start_stream_transcription(
        language_code="en-US",
        media_sample_rate_hz=SAMPLE_RATE,
        media_encoding="pcm",
    )

    async def write_chunks():
        # NOTE: For pre-recorded files longer than 5 minutes, the sent audio
        # chunks should be rate limited to match the realtime bitrate of the
        # audio stream to avoid signing issues.
        ts_files = get_ts_files_from_m3u8('stream/video.m3u8')

        async with aiofile.AIOFile(ts_files, "rb") as afp:
            reader = aiofile.Reader(afp)
            await apply_realtime_delay(
                stream, reader, BYTES_PER_SAMPLE, SAMPLE_RATE, CHANNEL_NUMS
            )

        await stream.input_stream.end_stream()

    handler = MyEventHandler(stream.output_stream)
    await asyncio.gather(write_chunks(), handler.handle_events())


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(basic_transcribe())
    loop.close()
