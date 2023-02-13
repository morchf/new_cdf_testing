/*
 * Source tables used in EVP metrics calculations
 */
--
--
--
/* Devices used in pilot study */
SELECT *
FROM evp.evp_devices;
/* Intersections */
SELECT *
FROM evp.evp_intersections;
/* Incidents */
SELECT *
FROM evp.evp_incidents;
/* Statically defined corridors */
SELECT *
FROM evp.evp_corridors
  LEFT JOIN evp.evp_intersections USING (location_id)
ORDER BY corridor_id,
  "sequence";
SELECT *
FROM mv_evp_corridors;
/*
 * Trips separated based on intersections passed-through
 * If a trip matches a corridor (all intersection in correct order)
 * the trip is marked with the corridor
 */
SELECT *
FROM evp.evp_corridors
  LEFT JOIN evp.evp_intersections USING (location_id)
ORDER BY corridor_id,
  "sequence";
SELECT *
FROM mv_evp_corridors;
/*
 * Parsed events
 * Combine devices used in study with raw GPS logs
 * Separate continuous logs into trips and tag events with nearby
 * intersection ID's
 */
SELECT *
FROM evp_events
LIMIT 100;