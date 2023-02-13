import boto3
import csv

# Create client here so that it will stay 'warm' between invocations saving execution time
s3 = boto3.resource("s3")


def lambda_handler(event, context):
    regions = ""
    agencies = ""
    vehicles = ""
    phase_selectors = ""
    communicators = ""
    locations = ""
    invalid_rows = ""

    # Get csv from bucket
    detail = event.get("detail")

    if detail:
        rp = detail.get("requestParameters")
    else:
        raise Exception("Input data lacks detail field, cannot download CSV from S3")

    if rp:
        bucket = rp.get("bucketName")
        key = rp.get("key")

        if not bucket:
            raise Exception(
                "Input data missing S3 bucket name, cannot download CSV from S3"
            )

        if not key:
            raise Exception("Input data missing S3 key, cannot download CSV from S3")

        tmpkey = key.replace("/", "")
        download_path = f"/tmp/{tmpkey}"
        s3.Object(bucket, key).download_file(download_path)
    else:
        raise Exception(
            "Input data missing requestParameters, cannot download CSV from S3"
        )

    # Open file and read rows
    with open(download_path, "r") as file:
        # For each row; save region, agency, vehicle and phase selector names for later deletion
        for row_cnt, row in enumerate(list(csv.reader(file, dialect="excel"))):
            if row[0] == "region" and row[1] != "name" and row[2] != "description":
                # region name is always the second column for regions
                regions, invalid_rows = validateAndSaveEntity(
                    f"{row[1]}", regions, row_cnt, invalid_rows
                )

            elif row[0] == "agency" and row[1] != "name" and row[2] != "region":
                # agency name is always the second column and region the third for agencies
                agencies, invalid_rows = validateAndSaveEntity(
                    f"{row[2]}/{row[1]}", agencies, row_cnt, invalid_rows
                )

            elif (
                (row[0] == "vehicle" or row[0] == "vehicleV2" or row[0] == "vehiclev2")
                and row[1] != "deviceid"
                and row[2] != "region"
            ):
                # deviceid always second column, region third, and agency fourth for vehicles
                vehicles, invalid_rows = validateAndSaveEntity(
                    f"{row[2]}/{row[3]}/{row[1]}", vehicles, row_cnt, invalid_rows
                )

            elif (
                row[0] == "phaseselector"
                and row[1] != "deviceid"
                and row[2] != "region"
            ):
                # deviceid always second column, region third, and agency fourth for phase selectors
                phase_selectors, invalid_rows = validateAndSaveEntity(
                    f"{row[2]}/{row[3]}/{row[1]}",
                    phase_selectors,
                    row_cnt,
                    invalid_rows,
                )

            elif (
                row[0] == "communicator" and row[1] != "deviceid" and row[2] != "region"
            ):
                # deviceid always second column, region third, and agency fourth for communicators
                communicators, invalid_rows = validateAndSaveEntity(
                    f"{row[2]}/{row[3]}/{row[1]}", communicators, row_cnt, invalid_rows
                )

            elif row[0] == "location":
                # assuming it is the header row of location
                if "region" in row and "agency" in row:
                    # get locationId or locationID
                    lower_row = [item.lower() for item in row]
                    index_location_id = lower_row.index("locationid")
                    index_region = lower_row.index("region")
                    index_agency = lower_row.index("agency")
                else:
                    locations, invalid_rows = validateAndSaveEntity(
                        f"{row[index_region]}/{row[index_agency]}/{row[index_location_id]}",
                        locations,
                        row_cnt,
                        invalid_rows,
                    )

            elif row[0] == "Done":
                break

            else:
                # first row is instructions but must be there and may change without notice
                # also ignore any header rows
                pass

        # send off found entities stripping off trailing comma before they go
        rc = {
            "regions": regions.rstrip(","),
            "agencies": agencies.rstrip(","),
            "vehicles": vehicles.rstrip(","),
            "phase_selectors": phase_selectors.rstrip(","),
            "communicators": communicators.rstrip(","),
            "locations": locations.rstrip(","),
            "invalid_rows": invalid_rows.rstrip(","),
        }
        print(rc)

    return rc


# check that entity string is valid i.e. follows region/agency/device format
def validateAndSaveEntity(entity_str, save_str, row_cnt, invalid_rows):
    rc = False
    txt = entity_str.split("/")
    for item in txt:
        if item == "":
            rc = False
            break
        else:
            rc = True

    if rc:
        save_str += f"{entity_str},"
    else:
        invalid_rows += f"{row_cnt},"

    return save_str, invalid_rows
