INSERT INTO evp.evp_corridors
SELECT *
FROM ext_evp.corridors AS d (
    corridor_id,
    corridor_name,
    "sequence",
    location_id
  )