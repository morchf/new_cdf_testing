import pytest
from unittest.mock import patch
from DataFiles2100 import DataFiles2100
import Config
import os
import shutil

logfilestring = """$GPVTG,170.9,T,,M,000.0,N,000.1,K,A*03
$GPRMC,155214.673,A,4457.01020,N,09257.16540,W,000.0,170.9,181016,,,A*76
$GPGSA,A,3,02,12,06,19,05,17,09,29,25,23,,,1.53,0.92,1.22*07
$GPGSV,3,1,11,02,82,325,48,12,61,252,49,06,50,056,45,25,37,306,45*71
$GPGSV,3,2,11,05,35,183,44,19,31,106,45,17,14,111,37,09,13,071,32*77
$GPGSV,3,3,11,29,11,297,44,23,07,041,42,31,02,337,29,,,,*47
$GPGGA,155215.673,4457.01020,N,09257.16540,W,1,10,0.92,00318.9,M,-032.3,M,,*63
$GPVTG,170.9,T,,M,000.0,N,000.1,K,A*03
$GPRMC,155215.673,A,4457.01020,N,09257.16540,W,000.0,170.9,181016,,,A*77
$GPGSA,A,3,02,12,06,19,05,17,09,29,25,23,,,1.53,0.92,1.22*07
$GPGSV,3,1,11,02,82,325,48,12,61,252,49,06,50,056,45,25,37,305,45*72
$GPGSV,3,2,11,05,35,183,44,19,31,106,45,17,14,111,38,09,13,071,32*78
$GPGSV,3,3,11,29,11,297,44,23,07,041,42,31,02,337,29,,,,*47
$GPGGA,155216.673,4457.01020,N,09257.16540,W,1,10,0.92,00318.9,M,-032.3,M,,*60
$GPVTG,170.9,T,,M,000.0,N,000.0,K,A*02
$GPRMC,155216.673,A,4457.01020,N,09257.16540,W,000.0,170.9,181016,,,A*74
"""
certstring = """-----BEGIN CERTIFICATE-----
MIID0DCCArigAwIBAgIBATANBgkqhkiG9w0BAQUFADB/MQswCQYDVQQGEwJGUjET
MBEGA1UECAwKU29tZS1TdGF0ZTEOMAwGA1UEBwwFUGFyaXMxDTALBgNVBAoMBERp
bWkxDTALBgNVBAsMBE5TQlUxEDAOBgNVBAMMB0RpbWkgQ0ExGzAZBgkqhkiG9w0B
CQEWDGRpbWlAZGltaS5mcjAeFw0xNDAxMjgyMDM2NTVaFw0yNDAxMjYyMDM2NTVa
MFsxCzAJBgNVBAYTAkZSMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJ
bnRlcm5ldCBXaWRnaXRzIFB0eSBMdGQxFDASBgNVBAMMC3d3dy5kaW1pLmZyMIIB
IjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvpnaPKLIKdvx98KW68lz8pGa
RRcYersNGqPjpifMVjjE8LuCoXgPU0HePnNTUjpShBnynKCvrtWhN+haKbSp+QWX
SxiTrW99HBfAl1MDQyWcukoEb9Cw6INctVUN4iRvkn9T8E6q174RbcnwA/7yTc7p
1NCvw+6B/aAN9l1G2pQXgRdYC/+G6o1IZEHtWhqzE97nY5QKNuUVD0V09dc5CDYB
aKjqetwwv6DFk/GRdOSEd/6bW+20z0qSHpa3YNW6qSp+x5pyYmDrzRIR03os6Dau
ZkChSRyc/Whvurx6o85D6qpzywo8xwNaLZHxTQPgcIA5su9ZIytv9LH2E+lSwwID
AQABo3sweTAJBgNVHRMEAjAAMCwGCWCGSAGG+EIBDQQfFh1PcGVuU1NMIEdlbmVy
YXRlZCBDZXJ0aWZpY2F0ZTAdBgNVHQ4EFgQU+tugFtyN+cXe1wxUqeA7X+yS3bgw
HwYDVR0jBBgwFoAUhMwqkbBrGp87HxfvwgPnlGgVR64wDQYJKoZIhvcNAQEFBQAD
ggEBAIEEmqqhEzeXZ4CKhE5UM9vCKzkj5Iv9TFs/a9CcQuepzplt7YVmevBFNOc0
+1ZyR4tXgi4+5MHGzhYCIVvHo4hKqYm+J+o5mwQInf1qoAHuO7CLD3WNa1sKcVUV
vepIxc/1aHZrG+dPeEHt0MdFfOw13YdUc2FH6AqEdcEL4aV5PXq2eYR8hR4zKbc1
fBtuqUsvA8NWSIyzQ16fyGve+ANf6vXvUizyvwDrPRv/kfvLNa3ZPnLMMxU98Mvh
PXy3PkB8++6U4Y3vdk2Ni2WYYlIls8yqbM4327IKmkDc2TimS8u60CT47mKU7aDY
cbTV5RDkrlaYwm5yqlTIglvCv7o==-----END CERTIFICATE-----"""
keystring = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAvpnaPKLIKdvx98KW68lz8pGaRRcYersNGqPjpifMVjjE8LuC
oXgPU0HePnNTUjpShBnynKCvrtWhN+haKbSp+QWXSxiTrW99HBfAl1MDQyWcukoE
b9Cw6INctVUN4iRvkn9T8E6q174RbcnwA/7yTc7p1NCvw+6B/aAN9l1G2pQXgRdY
C/+G6o1IZEHtWhqzE97nY5QKNuUVD0V09dc5CDYBaKjqetwwv6DFk/GRdOSEd/6b
W+20z0qSHpa3YNW6qSp+x5pyYmDrzRIR03os6DauZkChSRyc/Whvurx6o85D6qpz
ywo8xwNaLZHxTQPgcIA5su9ZIytv9LH2E+lSwwIDAQABAoIBAFml8cD9a5pMqlW3
f9btTQz1sRL4Fvp7CmHSXhvjsjeHwhHckEe0ObkWTRsgkTsm1XLu5W8IITnhn0+1
iNr+78eB+rRGngdAXh8diOdkEy+8/Cee8tFI3jyutKdRlxMbwiKsouVviumoq3fx
OGQYwQ0Z2l/PvCwy/Y82ffq3ysC5gAJsbBYsCrg14bQo44ulrELe4SDWs5HCjKYb
EI2b8cOMucqZSOtxg9niLN/je2bo/I2HGSawibgcOdBms8k6TvsSrZMr3kJ5O6J+
77LGwKH37brVgbVYvbq6nWPL0xLG7dUv+7LWEo5qQaPy6aXb/zbckqLqu6/EjOVe
ydG5JQECgYEA9kKfTZD/WEVAreA0dzfeJRu8vlnwoagL7cJaoDxqXos4mcr5mPDT
kbWgFkLFFH/AyUnPBlK6BcJp1XK67B13ETUa3i9Q5t1WuZEobiKKBLFm9DDQJt43
uKZWJxBKFGSvFrYPtGZst719mZVcPct2CzPjEgN3Hlpt6fyw3eOrnoECgYEAxiOu
jwXCOmuGaB7+OW2tR0PGEzbvVlEGdkAJ6TC/HoKM1A8r2u4hLTEJJCrLLTfw++4I
ddHE2dLeR4Q7O58SfLphwgPmLDezN7WRLGr7Vyfuv7VmaHjGuC3Gv9agnhWDlA2Q
gBG9/R9oVfL0Dc7CgJgLeUtItCYC31bGT3yhV0MCgYEA4k3DG4L+RN4PXDpHvK9I
pA1jXAJHEifeHnaW1d3vWkbSkvJmgVf+9U5VeV+OwRHN1qzPZV4suRI6M/8lK8rA
Gr4UnM4aqK4K/qkY4G05LKrik9Ev2CgqSLQDRA7CJQ+Jn3Nb50qg6hFnFPafN+J7
7juWln08wFYV4Atpdd+9XQECgYBxizkZFL+9IqkfOcONvWAzGo+Dq1N0L3J4iTIk
w56CKWXyj88d4qB4eUU3yJ4uB4S9miaW/eLEwKZIbWpUPFAn0db7i6h3ZmP5ZL8Q
qS3nQCb9DULmU2/tU641eRUKAmIoka1g9sndKAZuWo+o6fdkIb1RgObk9XNn8R4r
psv+aQKBgB+CIcExR30vycv5bnZN9EFlIXNKaeMJUrYCXcRQNvrnUIUBvAO8+jAe
CdLygS5RtgOLZib0IVErqWsP3EI1ACGuLts0vQ9GFLQGaN1SaMS40C9kvns1mlDu
LhIhYpJ8UsCVt5snWo2N+M+6ANh5tpWdQnEK6zILh4tRbuzaiHgb
-----END RSA PRIVATE KEY-----"""
rootcastring = """-----BEGIN CERTIFICATE-----
MIIDQTCCAimgAwIBAgITBmyfz5m/jAo54vB4ikPmljZbyjANBgkqhkiG9w0BAQsF
ADA5MQswCQYDVQQGEwJVUzEPMA0GA1UEChMGQW1hem9uMRkwFwYDVQQDExBBbWF6
b24gUm9vdCBDQSAxMB4XDTE1MDUyNjAwMDAwMFoXDTM4MDExNzAwMDAwMFowOTEL
MAkGA1UEBhMCVVMxDzANBgNVBAoTBkFtYXpvbjEZMBcGA1UEAxMQQW1hem9uIFJv
b3QgQ0EgMTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALJ4gHHKeNXj
ca9HgFB0fW7Y14h29Jlo91ghYPl0hAEvrAIthtOgQ3pOsqTQNroBvo3bSMgHFzZM
9O6II8c+6zf1tRn4SWiw3te5djgdYZ6k/oI2peVKVuRF4fn9tBb6dNqcmzU5L/qw
IFAGbHrQgLKm+a/sRxmPUDgH3KKHOVj4utWp+UhnMJbulHheb4mjUcAwhmahRWa6
VOujw5H5SNz/0egwLX0tdHA114gk957EWW67c4cX8jJGKLhD+rcdqsq08p8kDi1L
93FcXmn/6pUCyziKrlA4b9v7LWIbxcceVOF34GfID5yHI9Y/QCB/IIDEgEw+OyQm
jgSubJrIqg0CAwEAAaNCMEAwDwYDVR0TAQH/BAUwAwEB/zAOBgNVHQ8BAf8EBAMC
AYYwHQYDVR0OBBYEFIQYzIU07LwMlJQuCFmcx7IQTgoIMA0GCSqGSIb3DQEBCwUA
A4IBAQCY8jdaQZChGsV2USggNiMOruYou6r4lK5IpDB/G/wkjUu0yKGX9rbxenDI
U5PMCCjjmCXPI6T53iHTfIUJrU6adTrCC2qJeHZERxhlbI1Bjjt/msv0tadQ1wUs
N+gDS63pYaACbvXy8MWy7Vu33PqUXHeeE6V/Uq2V8viTO96LXFvKWlJbYK8U90vv
o/ufQJVtMVT8QtPHRh8jrdkPSHCa2XV4cdFyQzR1bldZwgJcJmApzyMZFo6IQ6XU
5MsI+yMRQ+hDKXJioaldXgjUkK642M4UwtBV8ob2xJNDd2ZhwLnoQdeXeGADbkpy
rqXRfboQnoZsG4q5WTP468SQvvG5
-----END CERTIFICATE-----"""

Config.AGENCY_GUID = "UnitTestAgencyGuid"
Config.ENDPOINT = "UnitTestNonExistantEndpoint"
Config.CERT_FILE = "temp_cert.pem"
Config.PRIVATEKEY_FILE = "temp_key.key"
Config.ROOTCA_FILE = "temp_rootCA.pem"

vehsns = None


class mock_class:
    publishes = []

    def __init__(val1, val2):
        pass

    def tls_set(self, ca_certs, certfile, keyfile, cert_reqs, tls_version):
        pass

    def connect(self, endpoint, port, timeout):
        pass

    def publish(self, topic, message):
        self.publishes.append((topic, message))

    def disconnect(self):
        pass


@pytest.fixture(autouse=True)
def setupAndTeardown():
    # SETUP
    try:
        shutil.rmtree("Temp")
    except FileNotFoundError:
        pass
    os.mkdir("Temp")
    os.chdir("Temp")

    with open("test.log", "w+") as f:
        f.write(logfilestring)
    with open("../temp_cert.pem", "w+") as f:
        f.write(certstring)
    with open("../temp_key.key", "w+") as f:
        f.write(keystring)
    with open("../temp_rootCA.pem", "w+") as f:
        f.write(rootcastring)
    with open("temp_cert.pem", "w+") as f:
        f.write(certstring)
    with open("temp_key.key", "w+") as f:
        f.write(keystring)
    with open("temp_rootCA.pem", "w+") as f:
        f.write(rootcastring)

    df = DataFiles2100(
        logFiles={"test.log": -1},
        vehVehIDs=[101, 102],
        startingVehSN=2222,
        vehRSSI=3456,
        vehGPSCStat=1,
        vehGPSSatellites=10,
        vehCityID=13,
        priority=1,
        opStatus=1,
        turn=2,
        vehClass=10,
        conditionalPriority=0,
        vehDiagValue=0,
    )
    global vehsns
    vehsns = df.write2100DataFiles()

    yield

    # TEARDOWN
    os.chdir("..")
    shutil.rmtree("Temp")
    os.remove("temp_cert.pem")
    os.remove("temp_key.key")
    os.remove("temp_rootCA.pem")


def test_simulate():
    global vehsns
    with patch("paho.mqtt.client.Client", new=mock_class) as my_mock_class:
        from Simulator2100 import Simulator2100

        sim = Simulator2100(
            vehsns=vehsns,
            ids=[101, 102],
            agencyGuid="UnitTestAgencyGuid",
            endpoint="UnitTestNonExistantEndpoint",
            cert="temp_cert.pem",
            key="temp_key.key",
            rootca="temp_rootCA.pem",
            directToPhaseSelector=False,
            verbose=0,
        )
        sim.simulate()

    assert len(my_mock_class.publishes) == 6
    expectedMessages = [
        (
            "GTT/UnitTestAgencyGuid/VEH/EVP/2100/2222/RTRADIO",
            "af080000800d0000f615a802fa777bfa005501000a00000065000d260a00000000000000",
        ),
        (
            "GTT/UnitTestAgencyGuid/VEH/EVP/2100/2222/RTRADIO",
            "af080000800d0000f615a802fa777bfa005501000a00000065000d260a00000000000000",
        ),
        (
            "GTT/UnitTestAgencyGuid/VEH/EVP/2100/2222/RTRADIO",
            "af080000800d0000f615a802fa777bfa005501000a00000065000d260a00000000000000",
        ),
        (
            "GTT/UnitTestAgencyGuid/VEH/EVP/2100/2223/RTRADIO",
            "b0080000800d0000f615a802fa777bfa005501000a00000066000d260a00000000000000",
        ),
        (
            "GTT/UnitTestAgencyGuid/VEH/EVP/2100/2223/RTRADIO",
            "b0080000800d0000f615a802fa777bfa005501000a00000066000d260a00000000000000",
        ),
        (
            "GTT/UnitTestAgencyGuid/VEH/EVP/2100/2223/RTRADIO",
            "b0080000800d0000f615a802fa777bfa005501000a00000066000d260a00000000000000",
        ),
    ]
    for i in expectedMessages:
        assert i in my_mock_class.publishes
