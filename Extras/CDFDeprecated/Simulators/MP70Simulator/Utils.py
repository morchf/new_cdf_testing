def ConvertToDD(deg, dir):
    DD = int(float(deg) / 100)
    MM = float(deg) - DD * 100
    DecD = DD + MM / 60
    if dir == "S" or dir == "W":
        DecD *= -1
    return DecD
