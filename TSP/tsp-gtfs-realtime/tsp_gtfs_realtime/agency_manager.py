import logging
import os
import signal
import sys
import time
from argparse import ArgumentParser
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Set

import boto3
import docker
import pause
from docker.models.containers import Container
from gtt.service.asset_library import AssetLibraryAPI, Device
from gtt.service.feature_persistence import FeaturePersistenceAPI
from pydantic import BaseModel

from gtt.data_model.asset_library import Template
from tsp_gtfs_realtime.core.aws import AWSRedisSubscriber
from tsp_gtfs_realtime.core.aws import Config as AWSConfig


class AgencySubscriber(AWSRedisSubscriber):
    def __init__(self, config, agency_name, vehicles=None, trips=None, **kwargs):
        super().__init__(config=config, **kwargs)
        self.agency_name = agency_name
        vehicle_channel_base = f"{self.agency_name}:new_vehicle_position"
        self.vehicles = vehicles
        # subscribe only to subset of vehicles if provided
        if self.vehicles:
            self.pubsub.subscribe(
                [f"{vehicle_channel_base}:{vehicle_id}" for vehicle_id in self.vehicles]
            )
        # else subscribe to all vehicles
        else:
            self.pubsub.psubscribe(f"{vehicle_channel_base}:*")
        if trips:
            logging.warning("managing based on trips not yet implemented")
        # FIFO queue
        self._prev_messages = []
        # used to set the update frequency to avoid container overload
        self._wait_until = 0

    def get_next_msg(self, queue_size=20, seconds_between=5, timeout=0.1) -> dict:
        """An abstraction around redis.pubsub.get_message()

        Adds ability to wait between accessing the next message while preventing
        messaging backup by building a FIFO queue and flushing the remaining messages.

        If seconds_between == None, it behaves just like get_message, except it ignores
        (un)subscribe messages on the channel and waits until it receives a data message


        Args:
            queue_size (int, optional):
                max size of FIFO queue. Defaults to 20.
            seconds_between (int, optional):
                time to pause between yielding each message. Defaults to 5.
            timeout (float, optional):
                time to wait for redis to provide a new message. Defaults to 0.1.

        Returns:
            dict: redis pubsub message dict
        """
        # just get next message of type message/pmessage
        if not seconds_between:
            while True:
                msg = self.pubsub.get_message(timeout=10)
                return msg if msg and "message" in msg.get("type") else None

        if self._wait_until > time.time():
            logging.info(f"waiting {(self._wait_until - time.time()):0.1f} seconds")
            pause.until(self._wait_until)

        # reset and refill the queue if publisher has fresh data
        count = 0
        msg = self.pubsub.get_message(timeout=timeout)
        if msg:
            while count < queue_size:
                msg = self.pubsub.get_message(timeout=0.1)
                if not msg:
                    break
                if "message" in msg.get("type"):
                    # FIFO
                    self._prev_messages = self._prev_messages[-queue_size:] + [msg]
                    count += 1
                    logging.debug(f"added {msg} to queue")
                else:
                    logging.debug(f"skipping {msg}")
            # flush the rest of the pubsub messages if we didn't timeout
            else:
                while self.pubsub.get_message(timeout=0.1):
                    pass
        # use the populated queue to provide the next message
        if self._prev_messages:
            vehicle_ids = [msg["channel"].split(":")[-1] for msg in self._prev_messages]
            logging.info(", ".join(vehicle_ids))
            self._wait_until = time.time() + seconds_between
            return self._prev_messages.pop(0)
        # unless queue has been emptied or never populated, then retry with backoff
        else:
            logging.info(f"timeout after {timeout} seconds with prev_messages empty")
            return self.get_next_msg(timeout=timeout * 2)


# ToDo: refactor and move to library module
class VehicleContainerManager:
    _running_containers: set

    def __init__(self):
        self._running_containers = set()

    def start_container(self, vehicle_id: str, environment: Dict[str, Any] = None):
        self._update_containers()

        if vehicle_id in self._get_stopped_vehicles():
            self._append_running_vehicles(vehicle_id)
            self._restart_container(vehicle_id=vehicle_id)
        elif vehicle_id not in self._get_running_vehicles():
            self._append_running_vehicles(vehicle_id)
            self._start_new_container(vehicle_id=vehicle_id, environment=environment)

    def _update_containers(self):
        pass

    def _get_stopped_vehicles(self) -> Set[str]:
        return set()

    def _get_running_vehicles(self) -> Set[str]:
        return self._running_containers.copy()

    def _append_running_vehicles(self, *vehicle_ids):
        self._running_containers.update(vehicle_ids)

    def _set_running_vehicles(self, vehicle_ids: Set[str]):
        self._running_containers = set(vehicle_ids)

    def _start_new_container(self, vehicle_id: str, environment: Dict[str, Any]):
        pass

    def _restart_container(self, vehicle_id: str):
        pass


class VehicleContainerManagerDocker(VehicleContainerManager):
    _container_name_base: str
    _client: docker.DockerClient
    _stopped_vehicles: Set[str]

    def __init__(
        self,
        container_name_base: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._container_name_base = (
            container_name_base or "tsp-gtfs-realtime_vehicle-manager"
        )
        self._client = docker.from_env()
        self._stopped_vehicles = set()

    def _start_new_container(self, vehicle_id: str, environment: Dict[str, Any]):
        container_name = self._get_container_name(vehicle_id)
        logging.info(f"creating and starting {container_name}")
        self._client.containers.run(
            image="tsp-gtfs-realtime_vehicle-manager:latest",
            name=container_name,
            labels={"type": "vehicle-manager", "vehicle_id": vehicle_id},
            remove=True,
            command=[
                "vehicle-manager",
                "--get-update-frequency",
            ],
            network="tsp-gtfs-realtime_default",
            environment=environment,
            detach=True,
        )

    def _restart_container(self, vehicle_id: str):
        container_name = self._get_container_name(vehicle_id)
        logging.info(f"restarting {container_name}")
        self._client.containers.get(container_name).start()

    def _get_container_name(self, vehicle_id):
        # docker name cannot have spaces. more string formatting might be required
        return f"{self._container_name_base}_{vehicle_id.replace(' ', '-')}"

    def _update_containers(self):
        containers: Iterable[Container] = self._client.containers.list(
            all=True,
            filters={"label": "type=vehicle-manager"},
        )
        running_vehicles = set(
            ctr.labels["vehicle_id"]
            for ctr in filter(lambda ctr: ctr.status == "running", containers)
        )
        stopped_vehicles = set(
            ctr.labels["vehicle_id"]
            for ctr in filter(lambda ctr: ctr.status != "running", containers)
        )
        logging.debug(f"{running_vehicles=}")
        logging.debug(f"{stopped_vehicles=}")
        self._set_running_vehicles(running_vehicles)
        self._stopped_vehicles = stopped_vehicles


class ECSConfig(BaseModel):
    subnet: str
    security_group: str
    cluster: str
    task_definition: str
    container: str

    @classmethod
    def from_env(cls) -> "ECSConfig":
        return cls(
            subnet=os.environ["VEHICLE_MANAGER_SUBNET"],
            security_group=os.environ["VEHICLE_MANAGER_SECURITY_GROUP"],
            cluster=os.environ["VEHICLE_MANAGER_CLUSTER"],
            task_definition=os.environ["VEHICLE_MANAGER_TASK_DEFINITION"],
            container=os.environ["VEHICLE_MANAGER_CONTAINER_NAME"],
        )


class VehicleContainerManagerECS(VehicleContainerManager):
    _client: Any
    _ecs_config: ECSConfig

    def __init__(self, ecs_config: Optional[ECSConfig] = None, **kwargs):
        super().__init__(**kwargs)
        self._client = boto3.client("ecs")
        self._ecs_config = ecs_config or ECSConfig.from_env()

    def start_container(self, vehicle_id=None, environment=None):
        if vehicle_id not in self._get_running_vehicles():
            logging.info(f"creating and starting {vehicle_id}")
            self._append_running_vehicles(vehicle_id)
            self._client.run_task(
                cluster=self._ecs_config.cluster,
                # ! This permission allows remote connections to containers, ok for prod?
                enableExecuteCommand=True,
                launchType="FARGATE",
                networkConfiguration={
                    "awsvpcConfiguration": {
                        # ! This option had to be enabled when testing elasticache on gttdev,
                        # ! but not when I was using my own VPC, should be possible to remove
                        "assignPublicIp": "ENABLED",
                        "subnets": [self._ecs_config.subnet],
                        "securityGroups": [self._ecs_config.security_group],
                    }
                },
                overrides={
                    "containerOverrides": [
                        {
                            "name": self._ecs_config.container,
                            "environment": [
                                dict(name=env_key, value=env_val)
                                for env_key, env_val in environment.items()
                            ],
                        },
                    ],
                },
                startedBy="agency_manager",
                tags=[
                    dict(key="tmp", value="delete_me"),
                ],
                taskDefinition=self._ecs_config.task_definition,
            )


def main():
    parser = ArgumentParser(description="Spawn new vehicle subscriber containers")
    parser.add_argument("--redis-url", type=str, help="hostname for redis endpoint")
    parser.add_argument("--redis-port", type=str, help="port for redis endpoint")
    parser.add_argument("--region-name", type=str, help="Region for CDF group path")
    parser.add_argument("--agency-name", type=str, help="Agency for CDF group path")
    parser.add_argument(
        "--vehicle-list",
        type=str,
        nargs="?",
        const=",",
        help="comma-delimited subset of vehicles to watch",
    )
    parser.add_argument(
        "--trip-list",
        type=str,
        nargs="?",
        const=",",
        help="comma-delimited subset of trips to watch",
    )
    parser.add_argument(
        "--seconds-between",
        type=int,
        default=0,
        help="seconds between spawning each vehicle to avoid overloading, default=5",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        help="the number of samples to get for each vehicle, default=10",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="the max time in seconds to wait for data before exiting, default=120",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="don't spawn containers, only test input and log",
    )
    parser.add_argument(
        "--get-statistics",
        action="store_true",
        help="prints various statistics",
    )
    parser.add_argument(
        "--should-query-docker",
        action="store_true",
        help="whether to query running/stopped containers",
    )
    parser.add_argument(
        "--should-restart",
        action="store_true",
        help="whether to query and restart stopped containers",
    )
    parser.add_argument("--local-development", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    # get from command line args or environment variables
    verbose_logging = args.verbose or ("VERBOSE_LOGGING" in os.environ)
    region_name = args.region_name or os.environ.get("REGION_NAME")
    agency_name = args.agency_name or os.environ.get("AGENCY_NAME")
    redis_url = args.redis_url or os.environ.get("REDIS_URL") or "localhost"
    redis_port = args.redis_port or os.environ.get("REDIS_PORT") or 6379

    # Fetch the agency details and form the agency path to query CDF for list of vehicles
    agency = AssetLibraryAPI().get_agency(region_name, agency_name)

    # Depending on the env variables, we can use the agency path if it means lesser
    # number of CDF calls or if the filter is not very reliable to search with
    # region_name = agency.region.name
    # agency_name = agency.name
    # agency_path = f"/{region_name}/{agency_name}"
    if args.vehicle_list is not None:
        vehicle_list = [vehicle for vehicle in args.vehicle_list.split(",") if vehicle]
    elif "VEHICLE_LIST" in os.environ:
        vehicle_list = [
            vehicle for vehicle in os.environ["VEHICLE_LIST"].split(",") if vehicle
        ]
    else:
        devices: List[Device] = agency.devices
        vehicle_list = [
            device.VID for device in devices if device.template_id == Template.Vehicle
        ]

    trip_list = (
        [trip for trip in args.trip_list.split(",") if trip]
        if args.trip_list is not None
        else [trip for trip in os.environ["TRIP_LIST"].split(",") if trip]
        if "TRIP_LIST" in os.environ
        else None
    )

    log_level = logging.DEBUG if verbose_logging else logging.INFO
    logging.basicConfig(level=log_level, format="%(message)s")
    logging.getLogger().setLevel(log_level)

    aws_cfg = AWSConfig(
        local_development=args.local_development,
        redis_url=redis_url,
        redis_port=redis_port,
    )
    logging.info(f"{aws_cfg=}")
    agency_subscriber = AgencySubscriber(aws_cfg, agency_name, vehicle_list, trip_list)

    # Cache vehicle list in redis set
    agency_subscriber.redis.sadd(
        f"tsp_in_cloud:supported_vehicle_ids:{agency.unique_id.lower()}", *vehicle_list
    )

    # Check if point-to-point agency
    try:
        is_point_to_point = FeaturePersistenceAPI().get_feature(
            agency_id=agency.unique_id.lower(),
            feature_name="tsp-asm-2101",
        )
    except Exception:
        is_point_to_point = False

    if is_point_to_point:
        logging.info(f"{agency_name} is a point-to-point agency. Running Dry-Run")
        args.dry_run = True

    if args.dry_run:
        vehicle_container_manager = VehicleContainerManager()
    elif args.local_development:
        vehicle_container_manager = VehicleContainerManagerDocker(
            should_query_docker=args.should_query_docker
        )
    else:
        vehicle_container_manager = VehicleContainerManagerECS()

    class SignalHandler:
        """registers double-acting signal handler

        1st occurrence sets a flag, `SignalHandler.signal_received` to be handled later
        2nd occurrence calls `sys.exit()`

        Args:
            signal_num (signal.Signals, optional):
                Signal to handle. Defaults to signal.SIGINT
        """

        def __init__(self, signal_num: signal.Signals = signal.SIGINT):
            self.signal_received = False
            self.name = signal_num.name
            signal.signal(signal_num, self.handler)

        def handler(self, signal_num, frame):
            logging.debug(f"{self.name} handler called with {signal_num=}, {frame=}")
            # if first signal received, exit after current loop iteration
            if not self.signal_received:
                logging.info(f"{self.name} received, exiting after main loop")
                self.signal_received = True
            # if a second signal received, explicitly exit
            else:
                logging.info(f"2nd {self.name} received, exiting now")
                sys.exit(1)

    interrupt_handler = SignalHandler(signal.SIGINT)

    if args.get_statistics:
        vehicle_counter = Counter()

    logging.info("starting main loop, waiting for first message")
    while not interrupt_handler.signal_received:
        msg = agency_subscriber.get_next_msg(seconds_between=args.seconds_between)
        if not msg:
            continue
        vehicle_id = msg["channel"].split(":")[-1]
        logging.debug(f"new msg with {vehicle_id=}")
        if args.get_statistics:
            vehicle_counter.update([vehicle_id])
        # if dry run, no containers are spawned
        if args.dry_run:
            continue
        # check for running/stopped containers by querying docker engine
        if args.should_query_docker:
            # ToDo: avoid querying list of running containers if possible
            vehicle_container_manager._update_containers()
        # restart vehicle manager if container exists, but is stopped
        if args.should_restart:
            vehicle_container_manager.restart_container(vehicle_id=vehicle_id)
        # create and start vehicle manager if container does not exist
        vehicle_container_manager.start_container(
            vehicle_id=vehicle_id,
            environment={
                "REDIS_URL": redis_url,
                "REDIS_PORT": redis_port,
                "REGION_NAME": region_name,
                "AGENCY_NAME": agency_name,
                "VEHICLE_ID": vehicle_id,
                # ToDo: remove device id format restriction by getting from agency.vehicles
                "CDF_DEVICE_ID": f"{agency_name}-gtfs-realtime-{vehicle_id}",
            },
        )

    logging.info("End of main loop, exiting")
    if args.get_statistics and vehicle_counter:
        logging.info("vehicle_position update counts")
        for vehicle_id, update_count in vehicle_counter.items():
            logging.info(f"  {vehicle_id}: {update_count}")


if __name__ == "__main__":
    main()
