def read_devicetable(cursor):
    cursor.execute("select Name, RegionId from dbo.Device")
    result = cursor.fetchall()
    return {"Name": [i.Name for i in result], "RegionId": [i.RegionId for i in result]}
