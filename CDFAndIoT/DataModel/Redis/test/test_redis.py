from typing import ClassVar

from gtt.data_model.redis import WILDCARD, RedisKey


class VehiclePositionsKey(RedisKey):
    prefix: ClassVar[str] = "tsp_in_cloud:vehicle_positions"

    agency: str
    trip: str
    vehicle: str


def test_redis_key():
    veh_pos_key = VehiclePositionsKey(
        agency="tsptest", trip="1234", vehicle="my-vehicle-id"
    )
    assert (
        veh_pos_key.key()
        == "tsp_in_cloud:vehicle_positions:agency:tsptest:trip:1234:vehicle:my-vehicle-id"
    )

    veh_pos_key = VehiclePositionsKey(agency=WILDCARD, trip="1234", vehicle=WILDCARD)

    assert (
        veh_pos_key.key()
        == "tsp_in_cloud:vehicle_positions:agency:*:trip:1234:vehicle:*"
    )

    assert (
        veh_pos_key.channel()
        == "tsp_in_cloud:vehicle_positions_new:agency:*:trip:1234:vehicle:*"
    )

    assert VehiclePositionsKey.parse_key(veh_pos_key.key()) == veh_pos_key
    assert VehiclePositionsKey.parse_key(veh_pos_key.channel()) == veh_pos_key
