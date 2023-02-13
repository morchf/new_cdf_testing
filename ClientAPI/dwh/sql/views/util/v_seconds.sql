-- Generator for all seconds in a day
-- 00:00:00 -> 23:59:59
CREATE VIEW v_seconds AS WITH n2 AS (
  SELECT
    0 g
  UNION
  ALL
  SELECT
    0
),
n4 AS (
  SELECT
    0 g
  FROM
    n2 A
    CROSS JOIN n2 b
),
n16 AS (
  SELECT
    0 g
  FROM
    n4 A
    CROSS JOIN n4 b
),
n256 AS (
  SELECT
    0 g
  FROM
    n16 A
    CROSS JOIN n16 b
),
n65536 AS (
  SELECT
    0 g
  FROM
    n256 A
    CROSS JOIN n256 b
),
n86400 AS (
  SELECT
    0 g
  FROM
    n65536 A
    CROSS JOIN n65536 b
  LIMIT
    86400
), seconds AS (
  SELECT
    ROW_NUMBER() OVER (
      ORDER BY
        (
          SELECT
            NULL
        )
    ) - 1 AS s
  FROM
    n86400
  ORDER BY
    s
)
SELECT
  DATEADD(SECOND, s, '00:00:00' :: TIME) AS s
FROM
  seconds