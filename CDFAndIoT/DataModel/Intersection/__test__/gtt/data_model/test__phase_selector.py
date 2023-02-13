from gtt.data_model.intersection import PhaseSelector, PhaseSelectorBuilder


class TestPhaseSelector:
    def test__phase_selector_builder__basic(self):
        messages = [
            {"serial_number": "one"},
            {"latitude": 49.8, "longitude": 123.1},
            {"make": "GTT", "model": "v764"},
        ]
        phase_selector_builder = PhaseSelectorBuilder()
        for message in messages:
            phase_selector_builder.add_partial(message)

        phase_selector = phase_selector_builder.build()

        assert phase_selector
        assert phase_selector.serial_number == "one"
        assert phase_selector.latitude == 49.8
        assert phase_selector.longitude == 123.1
        assert phase_selector.make == "GTT"
        assert phase_selector.model == "v764"

    def test__phase_selector__device_id_wild(self):
        phase_selector = PhaseSelector(serial_number="123")

        assert phase_selector is not None
        assert phase_selector.device_id == "FF000000"

    def test__phase_selector__device_id(self):
        phase_selector = PhaseSelector(serial_number="123", address="123")

        assert phase_selector is not None
        assert phase_selector.device_id == "FF800123"
