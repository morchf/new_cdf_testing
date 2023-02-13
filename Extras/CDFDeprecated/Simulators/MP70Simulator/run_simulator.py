import SimulatorMP70
import datetime

sim = SimulatorMP70.SimulateMP70Devices(
    logging=True,
    num_devices=2,
    # vehicleConfigs = [
    #     {
    #         "file_position": 402,
    #         "priority": "Low",
    #         "gpio": 11
    #     },
    #     {
    #         "file_position": 400
    #     },
    #     {
    #         "file_position": 401
    #     }
    # ],
    default={
        "file_position": 50,
        "gpio": 9,
        "priority": "High",
        "class": 10,
        "cert_filename": "",
        "key_filename": "",
        "cafile_filename": "",
        # "sim_file": "C:\\Users\\luke.schiefelbein\\Documents\\Projects\\MP70Simulator_Update\\Data\\GTTAroundOffice.log",
        "coordinates": [
            [32.684232, 83.128421],
            [32.684232, 83.127421],
            [32.683232, 83.127421],
        ],
        "speed": 10,
        "datetime": datetime.datetime.now(),
    },
)

sim.run()
