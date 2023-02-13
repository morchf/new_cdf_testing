CREATE OR REPLACE PROCEDURE testing.sp_test__f_duration ()
AS $$
BEGIN
  /* No duration */

  -- (First event in series)
  --       stop  drive
  --       1 --- 2

  CALL sp_assert(
    ABS(
      f_duration(
        NULL,
        'STOPPED_AT',
        'IN_TRANSIT_TO',
        NULL,
        '2021-01-01 12:00:01.000' :: TIMESTAMP,
        '2021-01-01 12:00:02.000' :: TIMESTAMP
      ) - 0
    ) < 0.0001
  );

  -- (Last event in series)
  -- same  same
  -- 0 --- 1

  CALL sp_assert(
    ABS(
      f_duration(
        'IN_TRANSIT_TO',
        'IN_TRANSIT_TO',
        NULL,
        '2021-01-01 12:00:01.000' :: TIMESTAMP,
        '2021-01-01 12:00:02.000' :: TIMESTAMP,
        NULL
      ) - 0
    ) < 0.0001
  );

  -- drive stop  drive
  -- 0 --- 1 --- 2

  CALL sp_assert(
    ABS(
      f_duration(
        'IN_TRANSIT_TO',
        'STOPPED_AT',
        'IN_TRANSIT_TO',
        '2021-01-01 12:00:00.000' :: TIMESTAMP,
        '2021-01-01 12:00:01.000' :: TIMESTAMP,
        '2021-01-01 12:00:04.000' :: TIMESTAMP
      ) - 0
    ) < 0.0001
  );

  /* Duration: 0 -> 1 */

  -- (Last event in series)
  -- stop  drive
  -- 0 --- 1
  -- |_____|

  CALL sp_assert(
    ABS(
      f_duration(
        'IN_TRANSIT_TO',
        'STOPPED_AT',
        'IN_TRANSIT_TO',
        '2021-01-01 12:00:00.000' :: TIMESTAMP,
        '2021-01-01 12:00:01.000' :: TIMESTAMP,
        '2021-01-01 12:00:04.000' :: TIMESTAMP
      ) - 0
    ) < 0.0001
  );

  /* Duration: 1 -> 2 */

  -- (First event in series)
  --       same  same
  --       1 --- 2
  --       |_____|

  CALL sp_assert(
    ABS(
      f_duration(
        NULL,
        'IN_TRANSIT_TO',
        'IN_TRANSIT_TO',
        NULL,
        '2021-01-01 12:00:01.000' :: TIMESTAMP,
        '2021-01-01 12:00:04.000' :: TIMESTAMP
      ) - 3
    ) < 0.0001
  );

  -- same  same  same
  -- 0 --- 1 --- 2
  --       |_____|

  CALL sp_assert(
    ABS(
      f_duration(
        'IN_TRANSIT_TO',
        'IN_TRANSIT_TO',
        'IN_TRANSIT_TO',
        '2021-01-01 12:00:00.000' :: TIMESTAMP,
        '2021-01-01 12:00:01.000' :: TIMESTAMP,
        '2021-01-01 12:00:04.000' :: TIMESTAMP
      ) - 3
    ) < 0.0001
  );

  CALL sp_assert(
    ABS(
      f_duration(
        'STOPPED_AT',
        'STOPPED_AT',
        'STOPPED_AT',
        '2021-01-01 12:00:00.000' :: TIMESTAMP,
        '2021-01-01 12:00:01.000' :: TIMESTAMP,
        '2021-01-01 12:00:04.000' :: TIMESTAMP
      ) - 3
    ) < 0.0001
  );

  /* Duration: 0 -> 2 */

  -- stop  drive drive
  -- 0 --- 1 --- 2
  -- |___________|

  CALL sp_assert(
    ABS(
      f_duration(
        'STOPPED_AT',
        'IN_TRANSIT_TO',
        'IN_TRANSIT_TO',
        '2021-01-01 12:00:00.000' :: TIMESTAMP,
        '2021-01-01 12:00:01.000' :: TIMESTAMP,
        '2021-01-01 12:00:04.000' :: TIMESTAMP
      ) - 4
    ) < 0.0001
  );

END;
$$ LANGUAGE plpgsql;

CALL testing.sp_test__f_duration();