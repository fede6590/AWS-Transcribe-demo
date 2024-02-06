FROM python:3.11-slim-bookworm

RUN useradd -m dev

WORKDIR /app

RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

USER dev

COPY requirements.txt .
COPY hls-stream.py .
COPY stream stream/

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

ENV AWS_ACCESS_KEY_ID="ASIAV7HSKFRHZOHRB73H"
ENV AWS_SECRET_ACCESS_KEY="LzzLhS1TbSntbrSE/RYA16aHMwLYJbdaph1Owzdk"
ENV AWS_SESSION_TOKEN="IQoJb3JpZ2luX2VjEPb//////////wEaCXVzLWVhc3QtMSJHMEUCIHTXy7PIaVBnEd/J8wRA9tR9aNCGTKzsbZ0Ez4KABvhaAiEA/6mHi2yiCbBJC09rC/5Ch8TNZnjArHkGjCbw4qHfVpMqnAMIv///////////ARABGgw0MTA2Nzc1NTQyNTUiDKGQNZUdWIj2lacb2irwApEAmPN6xkv13qey4E0l3Yir5n3n1ZVPTcXkC3M55h2eN1TBzoD4+pIEDMbAH0lSHAWIzRuRp7mDuZRGBYAu2PMBTiF2BEodCbQNdh9EHfTLv3C6QANmadDEujkfiOqm7zeZ/98JNhNyd/YKKYEr1l1JDeStE/chE79+ZZHxDkpxEtHUv0mAX7YraPtqP/+8KuXFBHGFy+E++fYEHq9ik80eJ2gNO+7oOV+VWYjrQSQ04il/c+uPO6MLM2SLHBMTvOKFfYPcVnL8KyIVOEQLgKx0Lnfr97ofamnhRF/W3AhCoMs3thXWeq1+nEJj9MmUyakQcqTmAPIBqwgJjq9SvWP8ypIym1t5RUVRhO8Shk8a5JBefZwPQ/xA5k33kkhO+1LPmNSVwL1vUMM+Ofasfy6F04UWjEQFoxmOHJI4zBTaZNAmbQhi+4XT+x59StQcPbgpM+98Q9fPtuqdsLrcHPHlUaw+zN/IyHJnIpkql3dRMPPoiK4GOqYBezEh5SsLSa3QfnqA2qXX1WQSwoXiUqrt/9glxaOL53wBqkpyILL4zOmCgVQSPMJptMEtJ9dd2XHfGNpKbPgLeqRLr6sUwrOT9JXRMpNogc7iEJ+FVWrJJM+3GqkET6+WqyXL0mf/StlgqLHverp+iBdUKwWpksASUcj+5TT9tOaVq8+Ho8V3bOhXmEpOEcdqnHPfLkuqexapfyWA7IbCr0tnf4zzJA=="

CMD ["python", "hls-stream.py"]