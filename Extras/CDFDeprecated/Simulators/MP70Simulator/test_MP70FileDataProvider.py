import pytest
import os
import sys
from MP70FileDataProvider import MP70FileDataProvider

path = None


def setup_module(module):
    print("Setting up test file...")
    global path
    path = os.path.join(os.path.dirname(sys.argv[0]), "testCase.txt")
    with open(path, "w") as f:
        f.write(
            "$GPRMC,155214.673,A,4457.01020,N,09257.16540,W,000.0,170.9,181016,,,A*76\n"
        )
        f.write(
            "$GPRMC,155215.673,A,4457.01020,N,09257.16540,W,000.0,170.9,181016,,,A*77\n"
        )


def teardown_module(module):
    print("Tearing down test file")
    global path
    os.remove(path)


def test_dataProvided():
    global path
    fp = MP70FileDataProvider(path, gpio=False, start="beginning")

    result = fp.get_record("123")
    keys = list(result.keys())
    assert len(keys) == 1
    assert abs(result[keys[0]]["atp.glat"] - 44.95016999999999) < 0.000001
    assert abs(result[keys[0]]["atp.glon"] + 92.95275666666666) < 0.000001
    assert abs(result[keys[0]]["atp.gspd"] - 0.0) < 0.000001
    assert abs(result[keys[0]]["atp.ghed"] - 170.9) < 0.000001

    result = fp.get_record("123")
    keys = list(result.keys())
    assert len(keys) == 1
    assert abs(result[keys[0]]["atp.glat"] - 44.95016999999999) < 0.000001
    assert abs(result[keys[0]]["atp.glon"] + 92.95275666666666) < 0.000001
    assert abs(result[keys[0]]["atp.gspd"] - 0.0) < 0.000001
    assert abs(result[keys[0]]["atp.ghed"] - 170.9) < 0.000001

    assert fp.get_record("123") is None


def test_startLocation():
    fp = MP70FileDataProvider(path, gpio=False, start="beginning")

    count = 0
    result = fp.get_record("123")
    while result is not None:
        count += 1
        result = fp.get_record("123")
    assert count == 2

    fp = MP70FileDataProvider(path, gpio=False, start="short")

    count = 0
    result = fp.get_record("123")
    while result is not None:
        count += 1
        result = fp.get_record("123")
    assert count == 1


def test_nodata():
    with pytest.raises(FileNotFoundError):
        MP70FileDataProvider("")
