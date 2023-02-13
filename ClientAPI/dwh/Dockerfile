ARG BASE_CONTAINER_REPO="docker.io"
FROM $BASE_CONTAINER_REPO/python:3.10-bullseye

RUN pip install --upgrade pip

RUN pip install boto3
RUN pip install psycopg2
RUN pip install --no-cache-dir --user docker

COPY sql/ /app
WORKDIR /app

ENV PYTHONUNBUFFERED=1

CMD ["python", "-u", "app.py"]
