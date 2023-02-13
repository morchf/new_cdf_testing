# GTFS Realtime Test Server

This service mocks the basic behavior of a GTFS Realtime feed, spies on IoT Core MQTT Messages,
and is able to run multi-step tests in order to test end-to-end behavior.
('end-to-end' meaning from the GTFS Realtime Feed to IoT Core)

### Server Listens on port `8080`!

## Env Vars

`MQTT_TOPICS`: a semicolon-separated list of MQTT topics to subscribe to. The test server will create a separate MQTT connection for each topic. This way, more than 100 messages total can be received per second, given that no more than 100 message are sent on each topic per second.

## Run with Docker:

```
$ docker build -t gtfs-realtie-test-server .
```

```
$ docker run -it --rm -p 8080:8080 stevenkaufman/mock-gtfs-realtime-server
```
