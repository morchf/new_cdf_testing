CREATE OR REPLACE FUNCTION f_lightbar_on (gpi FLOAT) RETURNS FLOAT IMMUTABLE as $$
  def convert_gpi(gpi):
    if gpi is not None:
        gpi = int(gpi)
        # use GPIO information
        ignition = gpi & 0x01
        left_turn = (gpi & 0x02) >> 1
        right_turn = (gpi & 0x04) >> 1  # shift only one for math below
        light_bar = (gpi & 0x08) >> 3
        disable = (gpi & 0x10) >> 4

        if light_bar and ignition:
          return 1

        op_status = 0
        # op status
        if not ignition or disable:
            op_status = 0
        elif light_bar and ignition and not disable:
            op_status = 1

        return op_status
    return -1.0
 
  return convert_gpi(gpi)
$$ LANGUAGE plpythonu;          