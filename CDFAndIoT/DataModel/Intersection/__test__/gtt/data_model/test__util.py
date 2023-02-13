from gtt.data_model.intersection.util import (
    coordinates_to_offset,
    offset_to_coordinates,
)


class TestUtil:
    def test__coordinates_to_offset__q1(self):
        x, y = coordinates_to_offset(0, 0, 1, 1)

        assert x == 110563.08458303248
        assert y == 111325.10434530996

    def test__coordinates_to_offset__q2(self):
        x, y = coordinates_to_offset(-1, 0, -2, 2)

        assert x == -110462.04694177733
        assert y == 222616.49469313462

    def test__coordinates_to_offset__q3(self):
        x, y = coordinates_to_offset(-1, -1, -4, -4)

        assert x == -331272.06154310546
        assert y == -334059.2520107312

    def test__coordinates_to_offset__q4(self):
        x, y = coordinates_to_offset(2, -2, 7, -7)

        assert x == 550648.0987546773
        assert y == -556958.1584746523

    def test__offset_to_coordinates__q1(self):
        lat, lon = offset_to_coordinates(0, 0, 100, 100)

        assert lat == 0.0009043694770123268
        assert lon == 0.0008983152841936246

    def test__offset_to_coordinates__q2(self):
        lat, lon = offset_to_coordinates(0, 0, -100, 100)

        assert lat == -0.0009043694770123268
        assert lon == 0.0008983152841936246

    def test__offset_to_coordinates__q3(self):
        lat, lon = offset_to_coordinates(0, 0, -100, -100)

        assert lat == -0.0009043694770123268
        assert lon == -0.0008983152841936246

    def test__offset_to_coordinates__q4(self):
        lat, lon = offset_to_coordinates(0, 0, 100, -100)

        assert lat == 0.0009043694770123268
        assert lon == -0.0008983152841936246

    def test__coords__basic(self):
        lat, lon = 13.501102678488419, 45.895064565921565
        lat2, lon2 = 13.5, 45.899997

        x, y = coordinates_to_offset(lat, lon, lat2, lon2)

        assert x == -122.00000000070885
        assert y == 534.0000000008973

    def test__offset__basic(self):
        lat, lon = offset_to_coordinates(
            13.5, 45.899997, -122.00000000070885, 534.0000000008973
        )

        assert lat == 13.501102678488419
        assert lon == 45.89506456592156
