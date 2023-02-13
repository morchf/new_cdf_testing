FROM python:3.10-bullseye

RUN pip install --upgrade pip
RUN pip install wheel

WORKDIR /tsp-gtfs-realtime
ENV PATH="/root/.local/bin:$PATH"

COPY ./requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY setup.py .
COPY tsp_gtfs_realtime/__init__.py ./tsp_gtfs_realtime/
COPY tsp_gtfs_realtime/core/*.py ./tsp_gtfs_realtime/core/
RUN pip install --no-cache-dir --user -e '.[all]'

COPY tsp_gtfs_realtime/*.py ./tsp_gtfs_realtime/
COPY tsp_gtfs_realtime/config/gtfs-realtime-api-poller.json ./tsp_gtfs_realtime/config/
COPY tools/recorded_data_publisher.py ./tools/
COPY data.parquet .

CMD /bin/bash
