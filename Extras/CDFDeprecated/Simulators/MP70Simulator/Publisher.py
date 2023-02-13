import paho.mqtt.client as mqtt
import threading
import os
import time


class Publisher:
    # ENDPOINT = os.environ["IOT_CORE_ENDPOINT"]
    ENDPOINT = None
    CERT_FILE = None
    ROOT_CA_FILE = None
    KEY_FILE = None

    PORT = 8883
    TIMEOUT = 60
    VERBOSE = 0

    def __init__(self, verbose=0):
        self.publisherThreads = []
        self.VERBOSE = verbose

    def __publisherThread__(
        self,
        clientId,
        topic,
        messages,
        endpoint,
        port,
        certfile,
        rootcafile,
        keyfile,
        timeout=60,
        delay=1,
        verbose=0,
    ):
        client = mqtt.Client(str(clientId))

        # Use Certs if provided
        if certfile is not None and rootcafile is not None and keyfile is not None:
            client.tls_set(
                ca_certs=rootcafile,
                certfile=certfile,
                keyfile=keyfile,
                cert_reqs=mqtt.ssl.CERT_REQUIRED,
                tls_version=mqtt.ssl.PROTOCOL_TLS,
            )

        if verbose:
            print(f"Client {clientId}:\t\tConnecting to broker at {endpoint}:{port}")

        client.connect(endpoint, port, timeout)

        client.loop_start()

        if verbose:
            print(f"Client {clientId}:\t\tConnected.  Starting to publish messages")

        totalMessageCount = len(messages)
        for messageIdx in range(len(messages)):
            if verbose:
                print(
                    f"Client {clientId}:\t\tPublishing message {messageIdx+1} of {totalMessageCount}: {messages[messageIdx]} under topic {topic}"
                )
            client.publish(topic, messages[messageIdx])
            time.sleep(delay)

        client.disconnect()

        if verbose:
            print(f"Client {clientId}:\t\tFinished publishing and disconnected")

    def setCertificates(self, certFile, rootCaFile, keyFile):
        if (
            not os.path.exists(certFile)
            or not os.path.exists(rootCaFile)
            or not os.path.exists(keyFile)
        ):
            raise IOError("Certificate files do not exist at the path specified")
        self.CERT_FILE = certFile
        self.ROOT_CA_FILE = rootCaFile
        self.KEY_FILE = keyFile

    def setEndpoint(self, endpoint):
        self.ENDPOINT = endpoint

    def setPort(self, port):
        if type(port) != int or port < 1 or port > 65535:
            raise ValueError("Invalid Port Number")
        self.PORT = port

    def createPublisher(self, clientId, topic, messages, delay=1):
        publisherThread = threading.Thread(
            target=self.__publisherThread__,
            args=(
                clientId,
                topic,
                messages,
                self.ENDPOINT,
                self.PORT,
                self.CERT_FILE,
                self.ROOT_CA_FILE,
                self.KEY_FILE,
                self.TIMEOUT,
                delay,
                self.VERBOSE,
            ),
        )
        publisherThread.start()
        self.publisherThreads.append(publisherThread)

    def close(self):
        for thread in self.publisherThreads:
            thread.join()
