from App import GetIotMqttCommCfg, GetDeviceCert, GetDeviceKey, GetCa, GetRootCa


def test_GetIotMqttCommCfg():
    result = GetIotMqttCommCfg("example-ats.iot.region-name.amazonaws.com")

    with open("TestData/IOTMQTTCommCfg", "rb") as expected:
        assert result == expected.read()


def test_GetIotMqttCommCfgBytes():
    result = GetIotMqttCommCfg(b"example-ats.iot.region-name.amazonaws.com")

    # with open("./IOTMQTTCommCfg", 'rb') as written:
    with open("TestData/IOTMQTTCommCfg", "rb") as expected:
        assert result == expected.read()


def test_GetDeviceCert():
    with open("TestData/deviceCert.crt", "r") as f:
        result = GetDeviceCert(f.read())

    with open("TestData/deviceCert", "rb") as expected:
        assert result == expected.read()


def test_GetDeviceCertBytes():
    with open("TestData/deviceCert.crt", "rb") as f:
        result = GetDeviceCert(f.read())

    with open("TestData/deviceCert", "rb") as expected:
        assert result == expected.read()


def test_GetDeviceKey():
    with open("TestData/deviceKey.key", "r") as f:
        result = GetDeviceKey(f.read())

    with open("TestData/deviceKey", "rb") as expected:
        assert result == expected.read()


def test_GetDeviceKeyBytes():
    with open("TestData/deviceKey.key", "rb") as f:
        result = GetDeviceKey(f.read())

    with open("TestData/deviceKey", "rb") as expected:
        assert result == expected.read()


def test_GetCa():
    with open("TestData/rootCA.crt", "r") as f:
        result = GetCa(f.read())

    with open("TestData/CA", "rb") as expected:
        assert result == expected.read()


def test_GetCaBytes():
    with open("TestData/rootCA.crt", "rb") as f:
        result = GetCa(f.read())

    with open("TestData/CA", "rb") as expected:
        assert result == expected.read()


def test_GetRootCa():
    with open("TestData/rootCA.crt", "r") as f:
        result = GetRootCa(f.read())

    with open("TestData/rootCA", "rb") as expected:
        assert result == expected.read()


def test_GetRootCaBytes():
    with open("TestData/rootCA.crt", "rb") as f:
        result = GetRootCa(f.read())

    with open("TestData/rootCA", "rb") as expected:
        assert result == expected.read()
