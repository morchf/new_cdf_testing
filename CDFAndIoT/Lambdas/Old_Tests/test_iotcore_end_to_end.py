"""
 MQTT client. 

 While this code includes MQTT pub and sub capabilities, only pub
 is used here. One connection to IoT Core is made, then multiple
 publishes are performed. 
 
 The main() function demonstrates intended use, provides sample data, 
 and serves as a functional test.

"""
import time
import datetime
import json
import paho.mqtt.client as mqtt
import ssl
import config

WAIT_SUB_MSG = 5  # Give time for MQTT subscribe to complete
WAIT_CONNECT = 5  # Give time for MQTT connect to complete
WAIT_CSR_REQUEST = 20  # Wait for CSR_request receive

# Use values from config file
cert_filename = config.cert_filename
key_filename = config.key_filename
cafile_filename = config.cafile_filename
logging = config.logging
client_id = config.client_id
endpoint = config.endpoint


class MQTTClient(mqtt.Client):
    """
    Class for Thing MQTT connection

    Note: A second instance of this class using an client_id with active
    connection connection closes the first connection. MQTT only allows one
    connection for a client id at a time.

    """

    def __init__(self, client_id=client_id, sub_topics=None, logging=logging):
        """
        Create the mqtt connection for a Thing
        """
        super().__init__(client_id=client_id)
        self.sub_flag = False
        self.pub_flag = False
        self.connect_flag = False
        self.disconnect_flag = False
        self.pub_msg_count = 0
        self.rcv_msg_count = 0
        self.logging = logging
        self.sub_topics = []
        if sub_topics:
            self.sub_topics += sub_topics
            if self.logging:
                print(self.sub_topics)

        try:
            self.mqttc = mqtt.Client(client_id=client_id)

            self.mqttc.on_log = self.on_log
            self.mqttc.on_connect = self.on_connect
            self.mqttc.on_disconnect = self.on_disconnect
            self.mqttc.on_message = self.on_message
            self.mqttc.on_publish = self.on_publish
            self.mqttc.on_subscribe = self.on_subscribe
            self.mqttc.on_unsubscribe = self.on_unsubscribe

            rc = self.mqttc.tls_set(
                certfile=cert_filename,
                keyfile=key_filename,
                ca_certs=cafile_filename,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2,
                ciphers=None,
            )

            if self.logging:
                print("MQTT tls_set rc = {}".format(rc))
                assert rc == ()

            rc = self.mqttc.connect(endpoint, 8883, 45)
            if self.logging:
                print("MQTT Connect rc = {}".format(rc))

            self.mqttc.loop_start()
            time.sleep(WAIT_CONNECT)
        except Exception as e:
            print("MQTT connect execption: {}".format(str(e)))
            self.mqttc = None

    def test_on_connect(self, mqttc, obj, flags, rc):
        if rc == 0:
            if self.sub_topics:
                self.mqtt_sub()
            self.connect_flag = True
            self.disconnect_flag = False
        if self.logging:
            print("on_connect, rc = {}".format(rc))

    def test_on_disconnect(self, mqttc, obj, rc):
        self.disconnect_flag = True
        self.connect_flag = False

        if self.logging:
            print("on_disconnect, rc = {}".format(rc))

    def test_on_message(self, mqttc, obj, msg):
        self.rcv_msg_count += 1
        if self.logging:
            print(
                "on_message: topic = {}, qos = {}, msg = {}".format(
                    msg.topic, msg.qos, msg.payload
                )
            )

    def on_publish(self, mqttc, obj, mid):
        self.pub_msg_count += 1
        self.pub_flag = False
        if self.logging:
            print("on_publish: mid: {}".format(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        self.sub_flag = True
        if self.logging:
            print("on_subscribe: mid = {}, granted qos = {}".format(mid, granted_qos))

    def on_unsubscribe(self, mqttc, userdata, mid):
        self.sub_flag = False
        if self.logging:
            print("on_subscribe: userdata = {}, mid = {}".format(userdata, mid))

    def on_log(self, mqttc, obj, level, string):
        if "CONNACK" in string:
            self.connect_flag = True
        if self.logging:
            print("log: msg: {}".format(string))
            print(
                "log flags: connect {}, disconnect {}, pub = {}, sub = {}, rcv cnt = {}, pub cnt = {}, ".format(
                    self.connect_flag,
                    self.disconnect_flag,
                    self.pub_flag,
                    self.sub_flag,
                    self.rcv_msg_count,
                    self.pub_msg_count,
                )
            )

    def mqtt_sub(self):
        """
        Subscribe to topics
        """
        for topic in self.sub_topics:
            try:
                if self.logging:
                    print("mqtt sub: {}".format(topic))
                self.sub_flag = True
                self.mqttc.subscribe(topic, qos=1)
            except Exception as e:
                print("MQTT Sub connect execption: {}".format(str(e)))

    def mqtt_unsub(self):
        """
        Unsubscribe to topics
        """
        for topic in self.sub_topics:
            try:
                if self.logging:
                    print("mqtt unsub: {}".format(topic))
                self.sub_flag = False
                self.mqttc.unsubscribe(topic)
                time.sleep(WAIT_SUB_MSG)
            except Exception as e:
                print("MQTT unsub connect execption: {}".format(str(e)))

    def mqtt_pub(self, topic, msg):
        """
        Publish msg to topic
        """

        if self.sub_topics:
            while not self.sub_flag:
                # wait for subscribe to complete
                time.sleep(WAIT_SUB_MSG)

        try:
            if self.logging:
                print("mqtt pub: topic = {}, msg = {}".format(topic, msg))
            self.pub_flag = True
            payload = json.dumps(msg, default=lambda x: x.__dict__)
            self.mqttc.publish(topic, payload, qos=1)
            time.sleep(WAIT_SUB_MSG)
        except Exception as e:
            print("MQTT Sub connect execption: {}".format(str(e)))

    def pre_processing_pub(self, value):
        # Remove data_format, add UTC
        mac_addr = value.get("mac", None)
        UTC = str(datetime.datetime.utcnow())
        value.update({"UTC": UTC})
        value.pop("data_format")
        if mac_addr:
            topic = "sensor_data/{}".format(mac_addr)
            self.mqtt_pub(topic, value)
        elif self.logging:
            print("Sensor data missing mac addr, don't pub")
        print(value)


def test_main():
    """
    Test MQTT client that sends sensor data.
    """

    value1 = {
        "data_format": 5,
        "humidity": 30.00,
        "temperature": 30.00,
        "pressure": 1017.11,
        "acceleration": 1034.3074977974393,
        "acceleration_x": 68,
        "acceleration_y": -12,
        "acceleration_z": 1032,
        "tx_power": 4,
        "battery": 2857,
        "movement_counter": 9,
        "measurement_sequence_number": 704,
        "mac": "F7:E3:69:3A:DC:5B",
    }
    value2 = {
        "data_format": 5,
        "humidity": 31.00,
        "temperature": 31.00,
        "pressure": 1017.11,
        "acceleration": 1034.3074977974393,
        "acceleration_x": 68,
        "acceleration_y": -12,
        "acceleration_z": 1032,
        "tx_power": 4,
        "battery": 2857,
        "movement_counter": 9,
        "measurement_sequence_number": 704,
        "mac": "F7:E3:69:3A:DC:5B",
    }
    value3 = {
        "data_format": 5,
        "humidity": 32.00,
        "temperature": 32.00,
        "pressure": 1017.11,
        "acceleration": 1034.3074977974393,
        "acceleration_x": 68,
        "acceleration_y": -12,
        "acceleration_z": 1032,
        "tx_power": 4,
        "battery": 2857,
        "movement_counter": 9,
        "measurement_sequence_number": 704,
        "mac": "F7:E3:69:3A:DC:5B",
    }

    # Three sets of values from the sensors
    values = [value1, value2, value3]

    # Connect to IoT Core
    mqtt_client = MQTTClient()
    if mqtt_client.connect_flag:
        # Pub values
        for value in values:
            mqtt_client.pre_processing_pub(value)

        mqtt_client.disconnect()
    elif logging:
        print("No MQTT Connection")


# if __name__ == "__main__":
#     main()
