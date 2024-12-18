FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ARG SERVICE_PORT
ENV SERVICE_PORT=${SERVICE_PORT}
EXPOSE ${SERVICE_PORT}
ARG SERVICE_HOST
ENV SERVICE_HOST=${SERVICE_HOST}

CMD uvicorn src.main:app --host $SERVICE_HOST --port $SERVICE_PORT --reload