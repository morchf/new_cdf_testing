def read_locationgrouptable(cursor):
    cursor.execute("select LocationGroupName from dbo.LocationGroup")
    result = cursor.fetchall()
    return {"LocationGroupName": [i.LocationGroupName for i in result]}
