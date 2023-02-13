ARG BASE_CONTAINER_REPO="docker.io"
ARG USERNAME="tsp"

# Base image
FROM ${BASE_CONTAINER_REPO}/python:3.10-slim-bullseye as builder

ARG USERNAME
RUN useradd -m ${USERNAME}
USER ${USERNAME}
WORKDIR /home/${USERNAME}

RUN pip install --user -U pip && pip install --user wheel

COPY --chown=${USERNAME}:${USERNAME} smart-city-platform    ./smart-city-platform
COPY core-requirements.txt  .

RUN pip install --user --no-cache-dir -r core-requirements.txt
RUN pip install --user --no-cache-dir --no-deps smart-city-platform/TSP/tsp-gtfs-realtime

ARG SERVICE_NAME
COPY ${SERVICE_NAME}-requirements.txt .
RUN pip install --user --no-cache-dir -r ${SERVICE_NAME}-requirements.txt


# Final image
FROM ${BASE_CONTAINER_REPO}/python:3.10-slim-bullseye

ARG USERNAME

COPY --from=builder /etc/passwd /etc/passwd
USER ${USERNAME}
WORKDIR /home/${USERNAME}

COPY --from=builder /home/${USERNAME}/.local /home/${USERNAME}/.local

ARG SERVICE_NAME

COPY smart-city-platform/TSP/tsp-gtfs-realtime/tsp_gtfs_realtime/${SERVICE_NAME}.py .
ENV SERVICE_NAME=${SERVICE_NAME}
CMD ["sh", "-c", "python ${SERVICE_NAME}.py"]
