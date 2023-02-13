import json
import logging


class EventBridgeTrigger:
    def __init__(self, events_client):
        self._events_client = events_client

    def invalidate_static_gtfs(self, agency_id: str):
        """
        Triggers an EventBridge event with the arguements passed

        Args:
            agency_id - The agency ID to invalidate static GTFS
        """
        entries = [
            {
                "DetailType": "json",
                "Detail": json.dumps({"agencyId": agency_id, "endpoint": "invalidate"}),
                "Source": "StaticGTFSPoller",
            },
        ]

        response = self._events_client.put_events(Entries=list(entries))

        if not response:
            raise Exception("Failed to send event")
        logging.debug(f"{response=}")

        if response["FailedEntryCount"] > 0:
            raise Exception(response["Entries"][0])
        if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
            if response["Entries"]:
                logging.error(f'{response["Entries"][0]}')
            raise Exception(f"Response from EventBridge: {response}")
        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            logging.info(f"Message sent to EventBridge. Response: {response}")
