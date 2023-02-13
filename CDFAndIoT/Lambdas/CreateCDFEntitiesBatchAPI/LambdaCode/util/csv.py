import cgi
import io
import math

SHEET_TYPE_MAP = {
    "Region (CS)": "region",
    "Agency (CS)": "agency",
    "Vehicles (CS)": "vehiclev2",
    "Devices (Ops)": "communicator",
    "Intersections (CS)": None,
    "Veh. > Device Assoc. (Ops)": None,
}

VALUE_TYPE_MAP = {
    "templateId": "templateId",
    # Region
    "Name": "name",
    "Description": "description",
    # Agency
    "Region": "region",
    "City": "city",
    "State": "state",
    "Time zone (Pacific/Mountain/Arizona/Central/Eastern)": "timezone",
    "GTT Agency code (valid values 2 -254)": "agencyCode",
    "Priority (High or Low)": "priority",
    # Vehicles (vehiclev2)
    "Agency": "agency",
    "Type (Values TBD)": "type",
    "GTT Class (1 to 10)": "class",
    "GTT Vehicle Id ( 2 to 9999)": "VID",
    # Devices (communicator)
    "Device": None,
    "Device Serial Number": "serial",
    "GTT Serial Number": "gttSerial",
    "LAN IP": "addressLAN",
    "Public IP": "addressWAN",
    "Make": "make",
    "Model": "model",
    "IMEI": "IMEI",
    "MAC Address": "addressMAC",
    # Intersections (location)
    "Intersection": "name",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "IP Address": None,
    "TC Make": None,
    "Firmware": None,
    # Vehicle > Device
    "GTT Vehicle ID (1 to 9999)": "deviceId",
}


def xlsx(file):
    """
    Parse XLSX files for raw values

    See: https://stackoverflow.com/questions/35744613/read-in-xlsx-with-csv-module-in-python
    """
    import zipfile
    from xml.etree.ElementTree import iterparse

    z = zipfile.ZipFile(file)
    strings = [
        el.text
        for e, el in iterparse(z.open("xl/sharedStrings.xml"))
        if el.tag.endswith("}t")
    ]

    sheet_entries = {}

    for e, el in iterparse(z.open("xl/workbook.xml")):
        if el.tag.endswith("}sheet"):  # <sheet name="XXX" />
            sheet_number = el.get("sheetId")
            sheet_name = el.get("name")

            sheet_entries[sheet_number] = sheet_name

    sheets = {}
    for sheet_number, sheet_name in sheet_entries.items():
        rows = []
        row = {}
        value = ""

        # Parse each row
        for e, el in iterparse(z.open(f"xl/worksheets/sheet{sheet_number}.xml")):
            if el.tag.endswith("}v"):  # <v>84</v>
                value = el.text
            if el.tag.endswith("}c"):  # <c r="A3" t="s"><v>84</v></c>
                if el.attrib.get("t") == "s":
                    value = strings[int(value)]
                letter = el.attrib["r"]  # AZ22
                while letter[-1].isdigit():
                    letter = letter[:-1]

                # Ignore empty values
                if not value or len(value) == 0 or value.strip() == 0 or value == "`":
                    continue

                row[letter] = value
                value = ""
            if el.tag.endswith("}row") and len(row) > 0:
                rows.append(row)
                row = {}

        if len(rows) <= 1:
            continue

        # Create key-value pairs from sheet header
        keys = list(rows[0].values())
        records = [
            {key: value for key, value in zip(keys, row.values()) if key is not None}
            for row in rows[1:]
        ]

        sheets[sheet_name] = records

    return sheets


def parse_form_data(body, headers):
    fp = io.BytesIO(body)
    contentType = (
        headers["Content-Type"]
        if headers.get("Content-Type")
        else headers["content-type"]
    )
    pdict = cgi.parse_header(contentType)[1]
    if "boundary" in pdict:
        pdict["boundary"] = pdict["boundary"].encode("utf-8")
    pdict["CONTENT-LENGTH"] = len(body)
    return cgi.parse_multipart(fp, pdict)


def read_excel(file):
    """Parse an Excel file

    Arguments:
        s {bytes} -- an Excel file

    Returns:
        list{dict} -- A dictionary with columns as keys and rows as values
    """
    data = xlsx(file)

    if not data or len(data.items()) == 0:
        return {}

    # Flatten record type map
    records = []
    for sheet_name, sheet_records in data.items():
        for sheet_record in sheet_records:
            # Map sheet names
            record_type = SHEET_TYPE_MAP.get(sheet_name, sheet_name.lower())
            records.append(
                {
                    record_type: record_type,
                    **sheet_record,
                }
            )

    return [
        {
            # Map key names
            VALUE_TYPE_MAP.get(k, k): int(v) if f"{v}".isdigit() else v
            for k, v in record.items()
        }
        for record in records
    ]


def read_csv(s, header=False):
    """Parse a CSV string of the below format

    key1,key2,key4,...\n
    value1,value2,value3,...\n
    key1',key2',key4',...\n
    value1',value2',value3',...[...\n]

    Arguments:
        s {string} -- a CSV in string format

    Returns:
        dict -- A dictionary with columns as keys and rows as values
    """

    # Remove header
    lines = s.splitlines()
    if header:
        lines = lines[1:]

    data = []
    for i in range(0, math.floor(len(lines) / 2) * 2, 2):
        # Map lines to key/value pairs, filtering improper records
        keys = [k for k in lines[i].split(",") if k != ""]
        values = [
            int(v) if isinstance(v, str) and v.isdigit() else v
            for v in lines[i + 1].split(",")
            if v != ""
        ]

        if not (len(keys) == len(values)):
            continue

        data.append({k: v for k, v in zip(keys, values)})

    return data
