import struct
import os
import shutil
import math
import Utils


class DataFiles2100:
    # RTRADIO Message Format
    FORMAT_RTRADIO = "IHxxiiBBHIHBBBBxxI"

    # Message Indicies
    LAT_IDX = 0
    LAT_NS_IDX = 1
    LON_IDX = 2
    LON_EW_IDX = 3

    # RMC Indicies
    RMC_LAT_IDX = 3
    RMC_NS_IDX = 4
    RMC_LON_IDX = 5
    RMC_EW_IDX = 6
    RMC_KNOTS_IDX = 7
    RMC_HEAD_IDX = 8

    # Enums
    PRIORITY_ENUM = [
        "High",
        "Low",
        "Probe",
        "Disabled",
        "Mapping",
        "Transit",
        "UNK_6",
        "UNK_7",
    ]
    OPSTATUS_ENUM = [
        "Priority Disabled",
        "Priority Enabled",
        "Mapping?",
        "Manual",
        "Diag Channel A",
        "Diag Channel B",
        "Diag Channel C",
        "Diag Channel D",
    ]
    TURN_ENUM = ["Straight", "Left", "Right", "UNK_3"]

    def __init__(
        self,
        logFiles,
        vehVehIDs,
        startingVehSN=1001,
        vehRSSI=0,
        vehGPSCStat=0,
        vehGPSSatellites=0,
        vehCityID=0,
        priority=0,
        opStatus=1,
        turn=0,
        vehClass=10,
        conditionalPriority=0,
        vehDiagValue=0,
    ):
        self.logFiles = logFiles
        self.vehVehIDs = vehVehIDs
        self.vehSN = startingVehSN
        self.vehRSSI = vehRSSI
        self.vehGPSCStat = vehGPSCStat
        self.vehGPSSatellites = vehGPSSatellites
        self.vehCityID = vehCityID
        self.vehModeOpTurn = (
            ((priority & 0x7) << 5) | ((opStatus & 0x7) << 2) | (turn & 0x3)
        )
        self.vehClass = vehClass
        self.conditionalPriority = conditionalPriority
        self.vehDiagValue = vehDiagValue

        if os.path.exists("Output"):
            shutil.rmtree("Output")
        os.makedirs("Output", exist_ok=True)

    def write2100DataFiles(self):
        vehSNs = []
        for vehVehID in self.vehVehIDs:
            # Get Log File and read RMC Messages
            file_name = self.__getNextFilename__()
            data = self.__readRMCMessages__(file_name)

            # Generate unique vehicle serial number
            vehSN = self.vehSN
            self.vehSN = self.vehSN + 1
            vehSNs.append(vehSN)

            topics, messages = self.__create2100DataMessages__(data, vehSN, vehVehID)

            self.__writeFile__(topics, messages, vehVehID, file_name)

        return vehSNs

    def __writeFile__(self, topics, messages, vehVehID, logFileName):
        filename = os.path.splitext(os.path.split(logFileName)[1])[0]
        with open(f"Output/{filename}_2100Messages{vehVehID}.csv", "w+") as f:
            f.write("\n".join([i.hex() for i in messages]))

        with open(f"Output/{filename}_2100Topics{vehVehID}.csv", "w+") as f:
            f.write("\n".join([i for i in topics]))

    def __getNextFilename__(self):
        for filename in self.logFiles:
            if self.logFiles[filename] != 0:
                self.logFiles[filename] = self.logFiles[filename] - 1
                return filename

    def __create2100DataMessages__(self, data, vehSN, vehVehID):
        messages2100, topics2100 = [], []
        for i in range(len(data)):
            replacementDataLine = data[i].split(",")

            # Find Lat and Lon
            vehGPSLat_ddmmmmmm = int(
                10000 * float(replacementDataLine[self.RMC_LAT_IDX])
            )
            vehGPSLon_dddmmmmmm = int(
                -10000 * float(replacementDataLine[self.RMC_LON_IDX])
            )

            vehGPSLat_degreedecimal = (
                math.modf(vehGPSLat_ddmmmmmm / 1000000)[1]
                + math.modf(vehGPSLat_ddmmmmmm / 1000000)[0] * 100 / 60
            )
            vehGPSLon_degreedecimal = (
                math.modf(vehGPSLon_dddmmmmmm / 1000000)[1]
                + math.modf(vehGPSLon_dddmmmmmm / 1000000)[0] * 100 / 60
            )

            latHighLow = (
                "L"
                if math.modf(abs(vehGPSLat_degreedecimal) * 100)[0] * 10 // 1 < 5
                else "H"
            )
            lonHighLow = (
                "L"
                if math.modf(abs(vehGPSLon_degreedecimal) * 100)[0] * 10 // 1 < 5
                else "H"
            )

            topicGpsStr = f"RTRADIO/{Utils.truncate(vehGPSLat_degreedecimal, 2)}{latHighLow},{Utils.truncate(vehGPSLon_degreedecimal, 2)}{lonHighLow}"

            # Find Velocity and Heading
            knotsToMps = 0.514444
            if replacementDataLine[self.RMC_HEAD_IDX] != "":
                vehGPSVel_mpsd5 = int(
                    float(replacementDataLine[self.RMC_KNOTS_IDX]) * knotsToMps * 5
                )
                vehGPSHdg_deg2 = int(float(replacementDataLine[self.RMC_HEAD_IDX]) / 2)
            else:
                vehGPSVel_mpsd5 = 0
                vehGPSHdg_deg2 = 0

            payload = struct.pack(
                self.FORMAT_RTRADIO,
                self.vehSN,
                self.vehRSSI,
                vehGPSLat_ddmmmmmm,
                vehGPSLon_dddmmmmmm,
                vehGPSVel_mpsd5 & 0xFF,
                vehGPSHdg_deg2 & 0xFF,
                self.vehGPSCStat & 0xFFFF,
                self.vehGPSSatellites,
                vehVehID & 0xFFFF,
                self.vehCityID & 0xFF,
                self.vehModeOpTurn & 0xFF,
                self.vehClass & 0xFF,
                self.conditionalPriority & 0xFF,
                self.vehDiagValue,
            )

            topics2100.append(topicGpsStr)
            messages2100.append(payload)

        return topics2100, messages2100

    def __readRMCMessages__(self, filename):
        rmcOnly = []

        try:
            f = open(filename, "r")

            replacementData = f.readlines()

            for i in range(len(replacementData)):
                if "RMC" in replacementData[i]:
                    rmcOnly.append(replacementData[i])
            return rmcOnly
        except IOError:
            print("Could not open file! ", filename)
            raise
