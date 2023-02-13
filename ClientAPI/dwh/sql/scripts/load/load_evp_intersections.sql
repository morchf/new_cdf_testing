INSERT INTO evp.evp_intersections
SELECT *
FROM ext_evp.intersections AS i (
    "name",
    intersection_id,
    latitude,
    longitude,
    cabinet,
    controller,
    intersection_number,
    controlelr_lan_ip,
    make,
    model,
    signal_core_serial_number,
    serial_number_764,
    lan_ip,
    miovision_ID,
    configured_764,
    approach_threshold_adjusted,
    notes
  )