FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY coordinator_project/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY coordinator_project/ /app/

EXPOSE 6380 8410

CMD ["python", "manage.py", "start_redis_proxy", "--redis-host", "redis", "--redis-port", "6379", "--proxy-port", "6380"]
