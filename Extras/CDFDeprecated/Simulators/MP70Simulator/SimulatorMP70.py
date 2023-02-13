import Config
from MP70CertProvider import MP70CertProvider
from MP70RandomDataProvider import MP70RandomDataProvider
from MP70FileDataProvider import MP70FileDataProvider
import GprmcSimulator
from Publisher import Publisher
import datetime
import os
import sys
import json


class SimulateMP70Devices:
    def __init__(
        self,
        logging=True,
        num_devices=3,
        vehicleConfigs=None,
        default={},
        createInCdf=True,
    ):
        self.logging = logging
        self.num_devices = num_devices
        self.vehicleConfigs = vehicleConfigs
        self.default = default
        self.createInCdf = createInCdf

        self.cert_provider = MP70CertProvider(self.logging)
        self.files_to_delete = []

        self.set_defaults(default)
        self.setup_vehicle_configs()

    def set_defaults(self, defaults):
        self.DEFAULT_FILE_POSITION = (
            "beginning"
            if not defaults.get("file_position")
            else defaults.get("file_position")
        )
        self.DEFAULT_GPIO = 9 if not defaults.get("gpio") else defaults.get("gpio")
        self.DEFAULT_CERTIFICATE_CERT_FILE = (
            None if not defaults.get("cert_filename") else defaults.get("cert_filename")
        )
        self.DEFAULT_CERTIFICATE_KEY_FILE = (
            None if not defaults.get("key_filename") else defaults.get("key_filename")
        )
        self.DEFAULT_CERTIFICATE_ROOTCA_FILE = (
            None
            if not defaults.get("cafile_filename")
            else defaults.get("cafile_filename")
        )
        self.DEFAULT_SPEED = 20 if not defaults.get("speed") else defaults.get("speed")
        self.DEFAULT_DATETIME = (
            datetime.datetime.now()
            if not defaults.get("datetime")
            else defaults.get("datetime")
        )
        self.DEFAULT_PRIORITY = (
            "High"
            if defaults.get("priority") not in ["High", "Low"]
            else defaults.get("priority")
        )
        self.DEFAULT_CLASS = (
            10
            if defaults.get("class") not in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            else defaults.get("class")
        )
        self.DEFAULT_COORDINATES = (
            None if not defaults.get("coordinates") else defaults.get("coordinates")
        )
        self.DEFAULT_SIMFILE = (
            None if not defaults.get("sim_file") else defaults.get("sim_file")
        )

    def setup_vehicle_configs(self):
        self.vehicleConfigs = [] if not self.vehicleConfigs else self.vehicleConfigs
        idx = self.num_devices - len(self.vehicleConfigs)
        if idx < 0:
            print("Warning: Some vehicle configs will be unused")
        for i in range(idx):
            self.vehicleConfigs.append({})

        for i in self.vehicleConfigs:
            i["file_position"] = (
                self.DEFAULT_FILE_POSITION
                if not i.get("file_position")
                else i.get("file_position")
            )
            i["gpio"] = self.DEFAULT_GPIO if not i.get("gpio") else i.get("gpio")
            i["cert_filename"] = (
                self.DEFAULT_CERTIFICATE_CERT_FILE
                if not i.get("cert_filename")
                else i.get("cert_filename")
            )
            i["key_filename"] = (
                self.DEFAULT_CERTIFICATE_KEY_FILE
                if not i.get("key_filename")
                else i.get("key_filename")
            )
            i["cafile_filename"] = (
                self.DEFAULT_CERTIFICATE_ROOTCA_FILE
                if not i.get("cafile_filename")
                else i.get("cafile_filename")
            )
            i["speed"] = self.DEFAULT_SPEED if not i.get("speed") else i.get("speed")
            i["datetime"] = (
                self.DEFAULT_DATETIME if not i.get("datetime") else i.get("datetime")
            )
            i["priority"] = (
                self.DEFAULT_PRIORITY if not i.get("priority") else i.get("priority")
            )
            i["class"] = self.DEFAULT_CLASS if not i.get("class") else i.get("class")
            i["coordinates"] = (
                self.DEFAULT_COORDINATES
                if not i.get("coordinates")
                else i.get("coordinates")
            )
            i["sim_file"] = (
                self.DEFAULT_SIMFILE if not i.get("sim_file") else i.get("sim_file")
            )

    def __get_certificates__(self):
        if self.num_devices == 1:
            try:
                result = {
                    "cert_filename": self.vehicleConfigs[0]["cert_filename"],
                    "key_filename": self.vehicleConfigs[0]["key_filename"],
                    "cafile_filename": self.vehicleConfigs[0]["cafile_filename"],
                    "device_name": self.vehicleConfigs[0]["device_name"],
                    "device_id": self.vehicleConfigs[0]["device_id"],
                }
                if self.logging:
                    print("Using manually specified certificates...")
                return [result]
            except Exception as e:
                print(e)

        if self.createInCdf:
            if self.logging:
                print("Using certificates from devices created in cdf...")
            return self.cert_provider.get_certs(self.num_devices, self.vehicleConfigs)
        else:
            try:
                result = []
                for i in self.vehicleConfigs:
                    result.append(
                        {
                            "cert_filename": i["cert_filename"],
                            "key_filename": i["key_filename"],
                            "cafile_filename": i["cafile_filename"],
                            "device_name": i["device_name"],
                            "device_id": i["device_id"],
                        }
                    )
                if self.logging:
                    print("Using manually specified certificates...")
                return result
            except Exception as e:
                print(e)

    def get_temp_file(self):
        i = 1
        while os.path.exists(
            os.path.join(os.path.dirname(sys.argv[0]), f"GPRMC_Simulation_file_{i}")
        ):
            i += 1
        return os.path.join(os.path.dirname(sys.argv[0]), f"GPRMC_Simulation_file_{i}")

    def parse_coordinates(self, idx):
        data_points = []
        if len(self.vehicleConfigs[idx]["coordinates"]) < 2:
            raise ValueError("Not enough data points for GPRMC Simulation")
        for i in range(len(self.vehicleConfigs[idx]["coordinates"]) - 1):
            data_points += GprmcSimulator.get_gprmc_messages(
                self.vehicleConfigs[idx]["coordinates"][i][0],
                self.vehicleConfigs[idx]["coordinates"][i][1],
                self.vehicleConfigs[idx]["coordinates"][i + 1][0],
                self.vehicleConfigs[idx]["coordinates"][i + 1][1],
                self.vehicleConfigs[idx]["speed"],
                self.vehicleConfigs[idx]["datetime"].strftime("%m/%d/%y"),
                self.vehicleConfigs[idx]["datetime"].strftime("%H:%M:%S"),
            )
        return data_points

    def get_data_provider(self, idx, method="GPRMC_SIMULATOR"):
        if method == "GPRMC_SIMULATOR":
            try:
                if self.logging:
                    print("Creating simulation file from input coordinates...")
                data = self.parse_coordinates(idx)

                filename = self.get_temp_file()
                with open(filename, "w") as f:
                    self.files_to_delete.append(filename)
                    for i in data:
                        f.write(f"{i}\n")

                dp = MP70FileDataProvider(
                    filename,
                    gpio=self.vehicleConfigs[idx]["gpio"],
                    start=self.vehicleConfigs[idx]["file_position"],
                )
                if self.logging:
                    print(
                        f"Using Simulation File created from input coordinates for simulation vehicle {idx}..."
                    )
            except Exception:
                return self.get_data_provider(idx, method="FILE_PROVIDER")
        elif method == "FILE_PROVIDER":
            try:
                dp = MP70FileDataProvider(
                    self.vehicleConfigs[idx]["sim_file"],
                    gpio=self.vehicleConfigs[idx]["gpio"],
                    start=self.vehicleConfigs[idx]["file_position"],
                )
                if self.logging:
                    print(
                        f"Using manually specified data file \"{self.vehicleConfigs[idx]['sim_file']}\" for simulation vehicle {idx}..."
                    )
            except Exception as e:
                print(e)
                return self.get_data_provider(idx, method="RANDOM")
        else:
            if self.logging:
                print(f"Using random sample data for simulation vehicle {idx}...")
            dp = MP70RandomDataProvider(50, gpio=self.vehicleConfigs[idx]["gpio"])

        return dp

    def run(self):
        # Create and download certs for x devices
        result = self.__get_certificates__()

        # Create a publisher for each vehicle
        publishers = Publisher(verbose=self.logging)
        publishers.setEndpoint(Config.ENDPOINT)
        for i in range(self.num_devices):
            try:
                deviceid = result[i]["device_id"].split("_")[-1]
                dp = self.get_data_provider(i)
                messages = []
                record = dp.get_record(deviceid)
                while record is not None:
                    messages.append(json.dumps(record))
                    record = dp.get_record(deviceid)

                publishers.setCertificates(
                    result[i]["cert_filename"],
                    result[i]["cafile_filename"],
                    result[i]["key_filename"],
                )
                publishers.createPublisher(
                    result[i]["device_name"], f"{deviceid}/messages/json", messages
                )
            except Exception as e:
                print(f"Exception occurred: {e}")

        publishers.close()
        self.cert_provider.close()
        for i in self.files_to_delete:
            os.remove(i)


def getNextData(dataSources):
    for dataSourceIdx in range(len(dataSources)):
        if dataSources[dataSourceIdx][2] != 0:
            dataSources[dataSourceIdx][2] = dataSources[dataSourceIdx][2] - 1
            return dataSources[dataSourceIdx]


if __name__ == "__main__":
    data = []
    devices = Config.DEVICES.split(",")
    certFile = Config.CERTFILE
    rootcaFile = Config.ROOTCAFILE
    keyFile = Config.KEYFILE
    createInCdf = False
    verbose = False

    i = 1
    while i < len(sys.argv):
        if "-d" == sys.argv[i] or "--devices" == sys.argv[i]:
            i = i + 1
            devices = sys.argv[i].split(",")
        elif "-c" == sys.argv[i] or "--cert-file" == sys.argv[i]:
            i = i + 1
            certFile = sys.argv[i]
        elif "-r" == sys.argv[i] or "--rootca-file" == sys.argv[i]:
            i = i + 1
            rootcaFile = sys.argv[i]
        elif "-k" == sys.argv[i] or "--key-file" == sys.argv[i]:
            i = i + 1
            keyFile = sys.argv[i]
        elif "--create-in-cdf" == sys.argv[i]:
            createInCdf = True
        elif "-v" == sys.argv[i] or "--verbose" == sys.argv[i]:
            verbose = True
        elif "-h" == sys.argv[i] or "--help" == sys.argv[i]:
            print(
                "MP70 Simulator (Commandline version)\n"
                "\n"
                "This tool can be used to simulate MP70 Devices publishing to an endpoint. "
                "Further configurations are allowed through the 'run_simulator.py' script.\n"
                "\n"
                "Options:\n"
                "-d,--devices:\ta comma seperated list of devices to simulate when publishing data to the endpoint. "
                "For example: --devices MP706544,MP706545\n"
                "-c,--cert-file:\tthe path to the certificate file\n"
                "-r,--rootca-file:\tthe path to the rootca file\n"
                "-k,--key-file:\tthe path to the private key file\n"
                "--create-in-cdf:\tif the devices simulated should be created in CDF. Default is not to create them\n"
                "-h,--help:\tprint this help message and exit\n"
                "\n"
                "Arguments:\n"
                "Arguments should be either the path to a file or a list of coordinates optionally followed by "
                "an equal sign and a number.  This specifies where the data is coming from (a file or generated "
                "by the code) and how many vehicles should run this data (if unspecified, any remaining vehicles "
                "will run the data.\n"
                "\n"
                "Example: GTTAroundOffice.log=10 37.84311,-122.343212,37.853541,-122.338274=15 EastBound.log"
                "\n"
                "Example Usage of Command Line Util:\n"
                "\tpython SimulatorMP70.py -d MP706544,MP706545 -c cert.pem -r rootca.pem -k key.key --create-in-cdf "
                "GTTAroundOffice.log=10 37.84311,-122.343212,37.853541,-122.338274=15 EastBound.log"
            )
            exit(0)
        else:
            details = sys.argv[i].split("=")
            pathCoord = details[0]
            quantity = -1 if len(details) == 1 else details[1]
            coords = []
            try:
                for val in zip(*[pathCoord.split(",")] * 2):
                    coords.append([float(val[0]), float(val[1])])
                data.append(["COORDINATES", coords, quantity])
            except Exception:
                data.append(["PATH", pathCoord, quantity])
        i = i + 1

    vehicleConfigs = []
    for veh in devices:
        datasource = getNextData(data)
        if datasource[0] == "PATH":
            vehicleConfigs.append(
                {
                    "cert_filename": certFile,
                    "key_filename": keyFile,
                    "cafile_filename": rootcaFile,
                    "device_name": veh,
                    "device_id": veh,
                    "sim_file": datasource[1],
                }
            )
        else:
            vehicleConfigs.append(
                {
                    "cert_filename": certFile,
                    "key_filename": keyFile,
                    "cafile_filename": rootcaFile,
                    "device_name": veh,
                    "device_id": veh,
                    "coordinates": datasource[1],
                }
            )

    simulator = SimulateMP70Devices(
        logging=verbose,
        num_devices=len(devices),
        vehicleConfigs=vehicleConfigs,
        createInCdf=createInCdf,
    )
    simulator.run()
