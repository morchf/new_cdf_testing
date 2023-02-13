import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from boto3.dynamodb.conditions import Key
from gtt.data_model.intersection import Intersection, PhaseSelector

from .phase_selector_service import PhaseSelectorService


class IntersectionService:
    def __init__(self, dynamodb_table, phase_selector_service: PhaseSelectorService):
        self._dynamodb_table = dynamodb_table
        self._phase_selector_service = phase_selector_service

    def list(
        self, agency_id, include_not_configured: Optional[bool] = False
    ) -> List[Intersection]:
        response = self._dynamodb_table.query(
            KeyConditionExpression=Key("agency_id").eq(agency_id)
        )
        items = response.get("Items")

        while "LastEvaluatedKey" in response:
            response = self._dynamodb_table.query(
                KeyConditionExpression=Key("agency_id").eq(agency_id),
                ExclusiveStartKey=response.get("LastEvaluatedKey"),
            )
            items += response.get("Items")

        intersections = []
        for item in items:
            try:
                intersection = Intersection(**item)

                if not include_not_configured and not intersection.is_configured:
                    continue

                intersections.append(intersection)
            except Exception as e:
                logging.error(
                    f"Failed to parse intersection SN={'N/A' if item is None else item.get('serial_number')}: {e}"
                )

        return intersections

    def get_not_configured(self, agency_id) -> Intersection:
        return next(
            filter(
                lambda i: not i.is_configured,
                self.list(agency_id=agency_id, include_not_configured=True),
            ),
            None,
        )

    def create(self, intersection: Intersection) -> Intersection:
        """Create an intersection in a DynamoDB table

        Args:
            intersection (Intersection): Intersection model

        Raises:
            ValueError: On invalid intersection response parsing

        Returns:
            Intersection: Inserted intersection
        """

        # Get existing intersections with name
        if (
            self.read_cache(intersection.agency_id, intersection.serial_number)
            is not None
        ):
            logging.debug(
                f"Existing intersection found with agency_id {intersection.agency_id} and serial number {intersection.serial_number}"
            )
            raise ValueError(
                "intersection with the same serial number already exists. Please use PUT method to update"
            )

        # Create new intersection
        return self.write(intersection)

    def reset(self, serial_number: str):
        """Reset cached intersection and device to defaults

        Args:
            serial_number (str): Intersection serial number
        """
        device_intersection = self.read(serial_number=serial_number)

        self._phase_selector_service.reset(
            device_intersection.ip_address, device_intersection.port
        )

        return self.read(serial_number=serial_number)

    def delete(self, agency_id: str, serial_number: str):
        """Delete cached intersection

        Args:
            serial_number (str): Intersection serial number
        """
        cached_intersection = self._read_cache(agency_id, serial_number)

        if cached_intersection is None:
            raise Exception(
                f"Device not found with agency id {agency_id=} and serial number {serial_number=}"
            )

        self._dynamodb_table.delete_item(
            Key={"agency_id": agency_id, "serial_number": serial_number}
        )

    def read(
        self,
        agency_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        ip_address: Optional[str] = None,
        port: Optional[int] = None,
    ) -> Intersection:
        """Read an intersection either directory or from cache and update cache

        Args:
            serial_number (Optional[str], optional): Intersection serial number. Defaults to None.
            ip_address (Optional[str], optional): Intersection IP address. Defaults to None.
            port (Optional[int], optional): Intersection port. Defaults to None.

        Raises:
            Exception: Raised on not found

        Returns:
            Intersection: Device intersection properties
        """
        try:
            intersection = None

            if serial_number is not None:
                intersection = Intersection(serial_number=serial_number)
                cached_intersection = self.read_cache(agency_id, serial_number)

                if (
                    cached_intersection is not None
                    and cached_intersection.ip_address is not None
                ):
                    ip_address = cached_intersection.ip_address
                if (
                    cached_intersection is not None
                    and cached_intersection.port is not None
                ):
                    port = cached_intersection.port

                if ip_address is None or port is None:
                    logging.error(f"No matching serial number: {serial_number}")

                if cached_intersection is None:
                    return None

                intersection = Intersection(
                    **cached_intersection.dict(exclude={"ip_address", "port"}),
                    ip_address=ip_address,
                    port=port,
                )

            if ip_address is None or port is None:
                raise ValueError(
                    "Must pass one of serial number or IP address and port"
                )

            device_phase_selector = self._phase_selector_service.read(ip_address, port)

            if not device_phase_selector:
                raise Exception(
                    f"Failed to connect to device {serial_number=}, {ip_address=}, {port=}"
                )
        except TimeoutError:
            raise TimeoutError
        except Exception as e:
            logging.error(f"Exception while reading configurations - {e}")
            raise Exception
        return self.write_cache(
            Intersection(
                **(
                    {}
                    if intersection is None
                    else intersection.dict(
                        exclude={"agency_id", "ip_address", "port", "serial_number"}
                    )
                ),
                # Override with device IP:port / serial number
                agency_id=agency_id,
                serial_number=device_phase_selector.serial_number,
                ip_address=ip_address,
                port=port,
            ),
            device_phase_selector,
        )

    def write(self, intersection: Intersection) -> Optional[Intersection]:
        """Write intersection to the device and update cache

        Args:
            intersection (Intersection): Update intersection

        Raises:
            Exception: Raised on not found
        """
        cached_intersection = self.read_cache(
            intersection.agency_id, intersection.serial_number
        )

        ip_address = intersection.ip_address
        port = intersection.port

        if cached_intersection is not None:
            ip_address = ip_address or cached_intersection.ip_address
            port = port or cached_intersection.port

        if ip_address is None or port is None:
            raise Exception("No matching cached intersection and no connection info")

        device_phase_selector = self._phase_selector_service.read(ip_address, port)

        if device_phase_selector is None:
            logging.error("Failed to read intersection")
            raise Exception(f"Failed with intersection SN={intersection.serial_number}")

        if cached_intersection is not None:
            # Handle 'last_communicated' field and conflicting values

            if not (
                Intersection(
                    **cached_intersection.dict(
                        exclude={"last_communicated", "ip_address", "port"}
                    )
                )
                == Intersection(
                    **device_phase_selector.dict(
                        exclude={"last_communicated", "ip_address", "port"}
                    )
                )
            ):
                logging.error("Cached intersection different than device intersection.")

        # Combine with device
        combined_intersection = Intersection.from_existing(
            device_phase_selector=device_phase_selector,
            intersection=intersection,
            cached_intersection=cached_intersection,
        )

        # Write to device
        self._phase_selector_service.write(
            ip_address,
            port,
            PhaseSelector(**combined_intersection.dict()),
        )

        # Read after write
        updated_device_phase_selector = self._phase_selector_service.read(
            ip_address, port
        )

        return self.write_cache(combined_intersection, updated_device_phase_selector)

    def _read_cache(self, agency_id, serial_number: str) -> Dict:
        return self._dynamodb_table.get_item(
            Key={"agency_id": agency_id, "serial_number": serial_number}
        ).get("Item")

    def read_cache(self, agency_id: str, serial_number: str) -> Intersection:
        cached_intersection = self._read_cache(agency_id, serial_number)

        if cached_intersection is None:
            return None

        try:
            return Intersection(**cached_intersection)
        except ValueError as e:
            logging.error(f"Invalid intersection retrieved from dynamo table: {e}")

            ip_address, port = cached_intersection.get(
                "ip_address"
            ), cached_intersection.get("port")
            if ip_address is None or port is None:
                logging.error("Intersection entry missing IP address and port")
                return None

            # Attempting to overwrite
            self.delete(serial_number)
            self.read(ip_address=ip_address, port=int(port))

            return None

    def write_cache(
        self, intersection: Intersection, phase_selector: Optional[PhaseSelector] = None
    ):
        intersection = Intersection(
            **{
                **({} if phase_selector is None else phase_selector.dict()),
                **(
                    {}
                    if intersection is None
                    else intersection.dict(
                        include={
                            "ip_address",
                            "port",
                            "intersection_id",
                            "intersection_name",
                            "serial_number",
                            "agency_id",
                        }
                    )
                ),
                "last_communicated": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            }
        )

        self._dynamodb_table.put_item(
            Item={
                **json.loads(intersection.json(), parse_float=Decimal),
            }
        )
        return intersection
