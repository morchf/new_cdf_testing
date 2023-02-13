ARG BASE_CONTAINER_REPO="docker.io"
ARG USERNAME="tsp"

FROM ${BASE_CONTAINER_REPO}/amazoncorretto:11-python3.10 as base

ARG USERNAME
RUN useradd -m ${USERNAME} || echo "User already exists"
RUN mkdir -p /home/${USERNAME}/.local
RUN chown ${USERNAME}: /home/${USERNAME}/.local

USER ${USERNAME}
WORKDIR /home/${USERNAME}

RUN python3 -m pip install --user -U pip && python3 -m pip install --user wheel

COPY --chown=${USERNAME}:${USERNAME} smart-city-platform ./smart-city-platform
COPY core-requirements.txt  .

RUN python3 -m pip install --user --no-cache-dir -r smart-city-platform/TSP/GTFSPoller/requirements.txt

FROM base

ARG USERNAME

COPY --from=base /etc/passwd /etc/passwd
USER ${USERNAME}
WORKDIR /home/${USERNAME}

COPY --from=base /home/${USERNAME}/.local /home/${USERNAME}/.local

ARG SERVICE_NAME

COPY smart-city-platform/TSP/GTFSPoller .

ENV SERVICE_NAME=${SERVICE_NAME}
CMD ["sh", "-c", "python3 ${SERVICE_NAME}.py"]
