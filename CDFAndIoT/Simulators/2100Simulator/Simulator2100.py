import os
import sys
from DataFiles2100 import DataFiles2100
import Config
import Utils
import Publisher


class Simulator2100:
    def __init__(
        self,
        vehsns,
        ids,
        agencyGuid,
        endpoint,
        cert,
        key,
        rootca,
        directToPhaseSelector,
        verbose,
    ):
        self.vehSerialNumbers = vehsns
        self.vehIds = ids
        self.agencyGuid = agencyGuid
        self.publisher = Publisher.Publisher(verbose=verbose)
        self.publisher.setEndpoint(endpoint)
        self.publisher.setCertificates(cert, rootca, key)
        self.directToPhaseSelector = directToPhaseSelector

    def findAndReadFile(self, nameToSearch):
        files = os.listdir("Output")
        filename = [name for name in files if nameToSearch in name][0]
        with open(f"Output/{filename}", "r") as f:
            if "Messages" in nameToSearch:
                data = [bytes.fromhex(line.strip()) for line in f.readlines()]
            else:
                data = [line.strip() for line in f.readlines()]
        return data

    def simulate(self):
        for vehIdx in range(len(self.vehIds)):
            vehId = self.vehIds[vehIdx]
            vehSn = self.vehSerialNumbers[vehIdx]
            messages = self.findAndReadFile(f"2100Messages{vehId}.csv")
            if self.directToPhaseSelector:
                topic = self.findAndReadFile(f"2100Topics{vehId}.csv")
                topic = [
                    f"GTT/{self.agencyGuid}/SVR/EVP/2100/{vehSn}/{i}" for i in topic
                ]
            else:
                topic = f"GTT/{self.agencyGuid}/VEH/EVP/2100/{vehSn}/RTRADIO"

            self.publisher.createPublisher(vehId, topic, messages)

        self.publisher.close()


if __name__ == "__main__":
    # Initial Values
    agencyGuid = Config.AGENCY_GUID
    endpoint = Config.ENDPOINT
    cert = Config.CERT_FILE
    rootca = Config.ROOTCA_FILE
    key = Config.PRIVATEKEY_FILE
    vehClass = Config.VEHICLE_CLASS
    vehAgency = Config.VEHICLE_AGENCY
    startingVehSN = Config.VEHICLE_SERIALNUMBER_START
    priority = Config.VEHICLE_PRIORITY
    opStatus = Config.VEHICLE_OPSTATUS
    turn = Config.VEHICLE_TURN_STATUS
    directToPhaseSelector = False
    vehIds = []
    dataFilenames = {}
    dataFilesOnly = False
    verbose = 0

    # Parse Commandline inputs
    try:
        i = 1
        while i < len(sys.argv):
            if "--help" == sys.argv[i] or "-h" == sys.argv[i]:
                with open("README.md", "r") as f:
                    print(f.read())
                exit(0)
            elif "--agency-guid" == sys.argv[i] or "-g" == sys.argv[i]:
                i = i + 1
                endpoint = sys.argv[i]
            elif "--endpoint" == sys.argv[i] or "-e" == sys.argv[i]:
                i = i + 1
                endpoint = sys.argv[i]
            elif "--cert" == sys.argv[i]:
                i = i + 1
                cert = sys.argv[i]
            elif "--rootca" == sys.argv[i]:
                i = i + 1
                rootca = sys.argv[i]
            elif "--key" == sys.argv[i]:
                i = i + 1
                key = sys.argv[i]
            elif "--class" == sys.argv[i] or "-c" == sys.argv[i]:
                i = i + 1
                vehClass = int(sys.argv[i])
            elif "--agency" == sys.argv[i] or "-a" == sys.argv[i]:
                i = i + 1
                vehAgency = int(sys.argv[i])
            elif "--priority" == sys.argv[i] or "-p" == sys.argv[i]:
                i = i + 1
                try:
                    priority = DataFiles2100.PRIORITY_ENUM.index(sys.argv[i])
                except Exception:
                    priority = int(sys.argv[i])
            elif "--opstatus" == sys.argv[i] or "-o" == sys.argv[i]:
                i = i + 1
                try:
                    opStatus = DataFiles2100.OPSTATUS_ENUM.index(sys.argv[i])
                except Exception:
                    opStatus = int(sys.argv[i])
            elif "--turn" == sys.argv[i] or "-t" == sys.argv[i]:
                i = i + 1
                try:
                    turn = DataFiles2100.TURN_ENUM.index(sys.argv[i])
                except Exception:
                    turn = int(sys.argv[i])
            elif "--ids" == sys.argv[i] or "-i" == sys.argv[i]:
                i = i + 1
                ids = sys.argv[i].split(",")
                for idRange in ids:
                    if "-" in idRange:
                        vehIds = vehIds + list(
                            range(
                                int(idRange.split("-")[0]),
                                int(idRange.split("-")[1]) + 1,
                            )
                        )
                    else:
                        vehIds.append(int(idRange))
            elif "--id-file" == sys.argv[i]:
                i = i + 1
                vehIds = Utils.parseCdfCsv(sys.argv[i])
            elif "--data-files-only" == sys.argv[i]:
                dataFilesOnly = True
            elif "--direct-to-phase-selector" == sys.argv[i]:
                directToPhaseSelector = True
            elif "--verbose" == sys.argv[i] or "-v" == sys.argv[i]:
                verbose = 1
            else:
                if "=" in sys.argv[i]:
                    filename = sys.argv[i].split("=")[0]
                    count = int(sys.argv[i].split("=")[1])
                    dataFilenames[filename] = count
                else:
                    dataFilenames[sys.argv[i]] = -1
            i = i + 1
    except Exception:
        print("Invalid Arguments!")
        with open("README.md", "r") as f:
            print(f.read())
        exit(1)

    # Create Data Files
    data = DataFiles2100(
        dataFilenames,
        vehIds,
        vehClass=vehClass,
        vehCityID=vehAgency,
        priority=priority,
        opStatus=opStatus,
        turn=turn,
    )
    serialNumbers = data.write2100DataFiles()

    if not dataFilesOnly:
        # Run Simulator
        sim = Simulator2100(
            serialNumbers,
            vehIds,
            agencyGuid,
            endpoint,
            cert,
            key,
            rootca,
            directToPhaseSelector,
            verbose,
        )
        sim.simulate()
