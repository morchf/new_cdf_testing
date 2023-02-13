CREATE OR REPLACE FUNCTION f_decode_longitude ("message" TEXT) RETURNS FLOAT IMMUTABLE as $$
  from decimal import Decimal
  import struct
  import math
  import codecs

  def dm_to_decimal_degree(degree):
      deg = math.trunc(degree)
      # Minutes shift over two decimal places and divide by 60
      MMmm = (abs(degree) - abs(deg)) * 100
      decimalDegree = deg + MMmm / 60

      if deg < 0:
          decimalDegree = deg - MMmm / 60
      elif deg == 0:
          if deg < 0:
              return -(MMmm / 60)
          else:
              return MMmm / 60
      return decimalDegree

  def display_longitude_from_raw(raw):
      MINLONGITUDE = -1800000
      MAXLONGITUDE = 1800000000
      if raw == -360:
          return ""
      dec = Decimal(raw * 0.000001)
      long = dm_to_decimal_degree(float(dec))
      if long > MAXLONGITUDE:
          return "{:.6f}".format(MAXLONGITUDE)
      if long < MINLONGITUDE:
          return "{:.6f}".format(MINLONGITUDE)
      return "{:.6f}".format(long)

  def decode_longitude(message):
    try:
      decoded_message = codecs.decode(codecs.encode(message),"base64")

      return float(display_longitude_from_raw(
          struct.unpack("<i", decoded_message[12:16])[0]
      ))
    except:
      return float(0)
 
  return decode_longitude(message)
$$ LANGUAGE plpythonu;          