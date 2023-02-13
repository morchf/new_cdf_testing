import json
import os
import argparse
import sys

sys.path.append(
    os.path.join(os.path.abspath(os.path.realpath(__file__) + 4 * "/.."), "CDFBackend")
)
from ui import list_regions, list_agencies, list_devices  # noqa: E402


def get_data():
    data = ""
    region_names = []
    agency_names = []

    # list all regions
    rc, region_list = list_regions()

    # rc True if any region exists
    if rc:
        # save data
        data = ",".join(json.dumps(r) for r in region_list)

        # find the names of each
        for region in region_list:
            region_names.append(region.get("name"))
        print(region_names)

    if region_names:
        # use names to see list their agencies
        for region in region_names:
            rc, agency_list = list_agencies(region)
            # rc returns True if any agency exists in that region
            if rc:
                data += ",".join(json.dumps(a) for a in agency_list)
                for agency in agency_list:
                    name = agency.get("name")
                    # save name as region/agency so that we can access it later
                    agency_names.append(f"{region}/{name}")
        print(agency_names)

    if agency_names:
        # use names to list all devices
        for agency in agency_names:
            region = agency.split("/")[0]
            agency = agency.split("/")[1]
            rc, device_list = list_devices(region, agency)
            if rc:
                data += ",".join(json.dumps(d) for d in device_list)

    return data


def save_to_file(data):
    # assume running in lambda; save file to /tmp
    fp = "/tmp/existing_entities.txt"

    # open file and write contents of data object
    with open(fp, "w") as file:
        file.write(data)
    # doing a write so explicitly call close
    file.close()


def main():
    argp = argparse.ArgumentParser(
        description="Get all entities in CDF and save to CSV file"
    )
    print(argp)
    data = get_data()

    save_to_file(data)


if __name__ == "__main__":
    main()
