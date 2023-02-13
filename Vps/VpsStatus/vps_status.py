"""
Created on Tue Feb 08 2021

@author: kinza.ahmed

The purpose of this script is to determine the health status of each vps that
is running. If the health status comes back as timed out, restart the vps.

Also utilized eric schneeberger's tcp ping logic.
"""

import socket
import binascii
import docker
import struct
import logging
import os
from argparse import ArgumentParser


def check_and_restart(should_check_ping, should_check_exited):
    """This function checks if the containers have exited or not. If it has
    it will restart it and it also pings each VPS and restarts them if they
    are not responding.

    Parameters
    ----------
    should_check_ping : boolean, flag to ping or not
    should_check_exited: boolean, flag to check if the containers have exited

    Return
    ------
    None
    """
    docker_client = docker.from_env()
    # restart stopped containers
    if should_check_exited:
        for ctr in docker_client.containers.list(filters={"status": "exited"}):
            logging.info(f"restarting {ctr.name}, status=={ctr.status}")
            docker_client.containers.get(ctr.name).start()
            logging.info(f"restart successful for: {ctr.name}")
    # ping running containers
    all_containers = docker_client.containers.list()
    if should_check_ping:
        for ctr in all_containers:
            if ctr.ports != {}:
                port = int(ctr.ports.get("5000/tcp")[0]["HostPort"])
                if not ping(port=port):
                    logging.info(f"restarting {ctr.name}, ping failed")
                    docker_client.containers.get(ctr.name).restart()
                    logging.info(f"restart successful for: {ctr.name}")
                else:
                    logging.info(f"ping was successful for: {ctr.name}")
    total_num_VPS = len(all_containers)
    logging.info(f"Checked {total_num_VPS} VPS")


def remove_scp_padding(data):
    """This function removes scp padding from the passed in data

    Parameters
    ----------
    data : binary data

    Return
    ------
    String of data.
    """
    data = data.replace(b"\x10\x10", b"\x10")
    return data


def decode(data, output=False):
    """This function decodes the binary data into a string and returns a response

    Parameters
    ----------
    data : binary data

    Return
    ------
    String of data.
    """
    data = remove_scp_padding(data)

    if data[1] == 0x91:  # Ping RSP
        Response = ("OK", "BAD")
        formatPing = ">xxxxxxBB10s5s5s5sBBBBBBHxxxx"
        if len(data) != struct.calcsize(formatPing):
            logging.info(f"Wrong size!!! {len(data)}")
            return
        (
            rsp,
            model,
            sn,
            ver,
            rev2,
            rev3,
            month,
            day,
            year,
            hours,
            minutes,
            seconds,
            status,
        ) = struct.unpack(formatPing, data)
        # Response[RSP] = OK
        return Response[rsp]


def ping(ip: str = "127.0.0.1", port: int = 2000) -> bool:
    """This function pings the VPS using a TCP connection

    ip : str, IPv4 Address (e.g., 3.86.39.209)
    port: int, PORT number (e.g., 2000)

    Return
    ------
    Boolean : returns True if the ping response was OK, false otherwise
    """
    try:
        TCP_IP = ip
        TCP_PORT = port
        BUFFER_SIZE = 1024
        PING = "1011FF80000001A01003"
        HEADER = "1011"
        WILDCARD = "FF800000"
        PAYLOAD = ""
        PING2 = HEADER + WILDCARD + PAYLOAD
        CHKSUM = 0
        for x in binascii.a2b_hex(PING2):
            CHKSUM += int(x)
        MESSAGE = PING
        data = []
        # TCP Connection  (Works)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect((TCP_IP, TCP_PORT))
        s.send(binascii.a2b_hex(MESSAGE))
        data = s.recv(BUFFER_SIZE)
        s.close()
        if decode(data) == "OK":
            return True
    except Exception as err:
        logging.info(f"An error occurred: {err.__str__()}")
        return False


# run based on command_line args
if __name__ == "__main__":
    parser = ArgumentParser(description="VPS container health check")
    parser.add_argument(
        "--skip-ping",
        action="store_true",
        help="tcp ping each running VPS container and restart on failure, default=False",
    )
    parser.add_argument(
        "--skip-exited",
        action="store_true",
        help="restart each VPS container that has exited, default=False",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    # get from command line args or environment variables
    verbose_logging = args.verbose or ("VERBOSE_LOGGING" in os.environ)
    should_check_ping = not ((args.skip_ping or ("SKIP_PING" in os.environ)))
    should_check_exited = not ((args.skip_exited or ("SKIP_EXITED" in os.environ)))
    log_level = logging.DEBUG if verbose_logging else logging.INFO
    logging.basicConfig(level=log_level, format="%(message)s")
    logging.getLogger().setLevel(log_level)
    # query VPS containers on local docker instance and restart if necessary
    check_and_restart(should_check_ping, should_check_exited)
