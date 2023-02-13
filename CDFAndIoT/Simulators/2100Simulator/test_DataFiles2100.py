import pytest
from DataFiles2100 import DataFiles2100
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
df = None


@pytest.fixture(autouse=True)
def setupAndTeardown():
    # SETUP
    global df

    try:
        shutil.rmtree("Temp")
    except FileNotFoundError:
        pass
    os.mkdir("Temp")
    os.chdir("Temp")

    with open("test.log", "w+") as f:
        f.write(logfilestring)

    df = DataFiles2100(
        logFiles={"test.log": -1},
        vehVehIDs=[101, 102, 110],
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

    yield

    # TEARDOWN
    os.chdir("..")
    shutil.rmtree("Temp")


def test_write2100DataFiles():
    global df
    df.write2100DataFiles()
    assert os.path.exists("Output/test_2100Messages101.csv")
    assert os.path.exists("Output/test_2100Topics101.csv")
    assert os.path.exists("Output/test_2100Messages102.csv")
    assert os.path.exists("Output/test_2100Topics102.csv")
    assert os.path.exists("Output/test_2100Messages110.csv")
    assert os.path.exists("Output/test_2100Topics110.csv")


def test_writeFile():
    global df
    df.__writeFile__(
        topics=["Example", "Topics"],
        messages=[b"Example", b"Messages"],
        vehVehID="321",
        logFileName="test.log",
    )
    assert os.path.exists("Output/test_2100Messages321.csv")

    f = open("Output/test_2100Messages321.csv", "r")
    data = f.read()
    f.close()
    assert data == "4578616d706c65\n4d65737361676573"

    f = open("Output/test_2100Topics321.csv", "r")
    data = f.read()
    f.close()
    assert data == "Example\nTopics"


def test_getNextFilename():
    global df
    assert df.__getNextFilename__() == "test.log"
    assert df.__getNextFilename__() == "test.log"


def test_create2100DataMessages():
    global df
    data = [
        "$GPRMC,155214.673,A,4457.01020,N,09257.16540,W,000.0,170.9,181016,,,A*76",
        "$GPRMC,155215.673,A,4457.01020,N,09257.16540,W,000.0,170.9,181016,,,A*77",
        "$GPRMC,155216.673,A,4457.01020,N,09257.16540,W,000.0,170.9,181016,,,A*74",
    ]
    topics, messages = df.__create2100DataMessages__(
        data=data, vehSN="101", vehVehID=123
    )

    assert len(topics) == 3
    assert topics[0] == "RTRADIO/44.95L,-92.95L"
    assert topics[1] == "RTRADIO/44.95L,-92.95L"
    assert topics[2] == "RTRADIO/44.95L,-92.95L"

    assert len(messages) == 3
    assert (
        messages[0]
        == b"\xae\x08\x00\x00\x80\r\x00\x00\xf6\x15\xa8\x02\xfaw{\xfa\x00U\x01\x00\n\x00\x00\x00{\x00\r&\n\x00\x00\x00\x00\x00\x00\x00"
    )
    assert (
        messages[1]
        == b"\xae\x08\x00\x00\x80\r\x00\x00\xf6\x15\xa8\x02\xfaw{\xfa\x00U\x01\x00\n\x00\x00\x00{\x00\r&\n\x00\x00\x00\x00\x00\x00\x00"
    )
    assert (
        messages[2]
        == b"\xae\x08\x00\x00\x80\r\x00\x00\xf6\x15\xa8\x02\xfaw{\xfa\x00U\x01\x00\n\x00\x00\x00{\x00\r&\n\x00\x00\x00\x00\x00\x00\x00"
    )


def test_readRmcMessages():
    global df
    messages = df.__readRMCMessages__("test.log")
    messages = [i.strip() for i in messages]
    assert messages == [
        "$GPRMC,155214.673,A,4457.01020,N,09257.16540,W,000.0,170.9,181016,,,A*76",
        "$GPRMC,155215.673,A,4457.01020,N,09257.16540,W,000.0,170.9,181016,,,A*77",
        "$GPRMC,155216.673,A,4457.01020,N,09257.16540,W,000.0,170.9,181016,,,A*74",
    ]
