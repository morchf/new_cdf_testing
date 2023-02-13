import math


def parseCdfCsv(filename):
    with open(filename, "r") as f:
        lines = f.readlines()

    ids = []
    for line in lines:
        if line.startswith("vehicleV2,") and not line.startswith("vehicleV2,deviceId"):
            ids.append(int(line.split(",")[9]))

    return ids


def truncate(number, digits):
    stepper = 10.0 ** digits
    return "{:.2f}".format(math.trunc(stepper * number) / stepper)


if __name__ == "__main__":
    result = parseCdfCsv("2100newval.csv")
    print(result)
