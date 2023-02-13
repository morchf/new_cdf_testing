INSERT INTO evp.evp_devices
SELECT *
FROM ext_evp.devices AS d (
    public_ip,
    "description",
    agency,
    device_serial_number,
    gtt_serial_number,
    lan_ip,
    make,
    model,
    imei,
    mac_address,
    factory_default_pw,
    sim_serial
  )