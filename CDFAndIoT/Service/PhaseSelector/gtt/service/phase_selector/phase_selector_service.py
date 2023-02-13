import logging
import socket
import time
from typing import Any, List, Optional, Tuple

from gtt.data_model.intersection import (
    READ_MESSAGES,
    RESET_MESSAGES,
    WRITE_MESSAGES,
    PhaseSelector,
    PhaseSelectorBuilder,
    PhaseSelectorMessage,
)


class PhaseSelectorService:
    BUFFER_SIZE = 4096
    TIMEOUT = 10
    RETRIES = 3

    def __init__(self, ssm, ec2, *, use_public_ip_addresses: Optional[bool] = False):
        self._ssm = ssm
        self._ec2 = ec2
        self._use_public_ip_addresses = use_public_ip_addresses

    def list_serial_numbers(
        self, instance_ids: List[str]
    ) -> List[Tuple[str, str, int]]:
        """Given a list of instances, get the serial numbers, IP addresses, and ports

        Args:
            instance_ids (List[str]): EC2 instance IDs

        Returns:
            List[Tuple[str, str, int]]]: List of serial numbers, IP addresses, and ports
        """
        logging.info(f"Listing serial numbers from {len(instance_ids)} instances")

        list_of_v764s = []
        for instance_id in instance_ids:
            logging.info(f"Sending command for instance ID: {instance_id}")
            response = self._ssm.send_command(
                InstanceIds=[instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={
                    "commands": [
                        'sudo docker ps --format "name={{.Names}} port={{.Ports}}"'
                    ]
                },
            )
            command_id = response["Command"]["CommandId"]
            time.sleep(1)

            logging.info("Retrieving response")
            output = self._ssm.get_command_invocation(
                CommandId=command_id, InstanceId=instance_id
            )
            try:
                logging.info("Sending command for IP addresses")
                instance = self._ec2.describe_instances(InstanceIds=[instance_id])[
                    "Reservations"
                ][0]["Instances"][0]
                ip_address = instance.get("PrivateIpAddress")

                if self._use_public_ip_addresses:
                    ip_address = instance.get("PublicIpAddress")
            except Exception as e:
                logging.error(f"Failed to query instance ID {instance_id} {e}")
                continue

            list_of_v764s.append((output["StandardOutputContent"], ip_address))
        individual_v764 = []
        connection_details = []
        for (i, ip_address) in list_of_v764s:
            individual_v764 = i.split("\n")
            for j in individual_v764:
                serial_number = j[j.find("name=") + 5 : j.find("port=") - 1]
                if serial_number == "ecs-agent" or not (serial_number):
                    continue
                port = int(j[j.find("0.0.0.0:") + 8 : j.find("0.0.0.0:") + 12])
                connection_details.append((serial_number, ip_address, port))
        return connection_details

    def get_connection(
        self, instance_ids: List[str], serial_number: str
    ) -> Optional[Tuple[str, int]]:
        connections = self.list_serial_numbers(instance_ids)
        connection = next(
            filter(
                lambda c: c[0] == serial_number,
                connections,
            ),
            None,
        )

        if connection is None:
            return None

        (_, ip_address, port) = connection
        return (ip_address, port)

    @classmethod
    def _open_socket(cls, ip_address: str, port: int):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # setting socket timeout
        s.settimeout(PhaseSelectorService.TIMEOUT)
        try:
            s.connect((ip_address, port))
        except TimeoutError:
            logging.error(
                f"Failed to connect to ip address - {ip_address} and port - {port}"
            )
            raise TimeoutError
        return s

    @classmethod
    def _send_message_packet(
        cls, s, ip_address, port, message, message_packet
    ) -> List[Any]:
        responses = []

        try:
            for i in range(0, cls.RETRIES):
                try:
                    logging.debug(f"Sending message {message_packet}")
                    s.send(message_packet)
                    data = s.recv(PhaseSelectorService.BUFFER_SIZE)
                    if len(data) == 0:
                        raise Exception("Null response received")
                    logging.debug(f"Response (length={len(data)}): {data} ")
                    responses.append((message.unpack(data), message))
                except TimeoutError:
                    logging.error(
                        "Timeout occurred while waiting for the response from the phase selector"
                    )
                    if s is not None:
                        s.close()
                    raise TimeoutError

                except IOError:
                    if s is not None:
                        s.close()

                    cls.wait()
                    s = cls._open_socket(ip_address, port)
                    continue

                except Exception as e:
                    logging.error(
                        f"Ran into error message ID 0x{message.id:02x}, retrying ({i + 1} / {cls.RETRIES}): {e}"
                    )
                    cls.wait()
                    raise Exception
                    continue

                # Stop retry iteration on successful unpack
                raise StopIteration

        except StopIteration:
            pass

        return responses

    @classmethod
    def wait(cls) -> None:
        time.sleep(0.125)

    @classmethod
    def send_messages(
        cls,
        ip_address: str,
        port: int,
        messages: List[PhaseSelectorMessage],
        phase_selector: Optional[PhaseSelector] = None,
    ) -> List[Any]:
        s = None
        try:
            s = cls._open_socket(ip_address, port)

            responses = []
            for message in messages:
                logging.debug(f"Sending message ID 0x{message.id:02x}")
                try:
                    message_packets = message.pack(phase_selector=phase_selector)
                except Exception as e:
                    logging.error(f"Error packing message ID 0x{message.id:02x}: {e}")
                    continue

                # Commands may be split into multiple messages
                for message_packet in (
                    [message_packets]
                    if isinstance(message_packets, bytes)
                    else message_packets
                ):
                    responses += cls._send_message_packet(
                        s,
                        ip_address,
                        port,
                        message,
                        message_packet,
                    )

            return responses
        except TimeoutError:
            logging.error("Timeout error occured in sendmessages")
            raise TimeoutError
        except Exception as e:
            logging.info(f"raising exception in send messages {e}")
            raise Exception
        finally:
            if s is not None:
                s.close()

    @classmethod
    def write(
        cls, ip_address: str, port: int, phase_selector: PhaseSelector
    ) -> List[Any]:
        if ip_address is None:
            raise ValueError("Missing IP address")
        if port is None:
            raise ValueError("Missing port")

        return PhaseSelectorService.send_messages(
            ip_address, port, WRITE_MESSAGES, phase_selector
        )

    @classmethod
    def reset(cls, ip_address: str, port: int) -> List[Any]:
        return PhaseSelectorService.send_messages(ip_address, port, RESET_MESSAGES)

    @classmethod
    def read(cls, ip_address: str, port: int) -> PhaseSelector:
        phase_selector_builder = PhaseSelectorBuilder()
        try:
            for (response, message) in PhaseSelectorService.send_messages(
                ip_address, port, READ_MESSAGES
            ):
                phase_selector_builder.add_partial(response, message)
        except TimeoutError:
            raise TimeoutError
        except Exception as e:
            logging.error(f"Exception in PhaseSelectorService read - {e}")
            raise Exception
        return phase_selector_builder.build()
