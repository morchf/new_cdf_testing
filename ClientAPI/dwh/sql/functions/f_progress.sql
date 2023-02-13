CREATE
OR REPLACE FUNCTION f_progress (
    previous_t TIMESTAMP,
    t TIMESTAMP,
    next_t TIMESTAMP
) RETURNS FLOAT STABLE AS $$
SELECT
    CASE
        WHEN EXTRACT(
            EPOCH
            FROM
                $3
        ) - EXTRACT(
            EPOCH
            FROM
                $1
        ) = 0 THEN 0
        ELSE (
            EXTRACT(
                EPOCH
                FROM
                    $2
            ) - EXTRACT(
                EPOCH
                FROM
                    $1
            )
        ) :: FLOAT / (
            EXTRACT(
                EPOCH
                FROM
                    $3
            ) - EXTRACT(
                EPOCH
                FROM
                    $1
            )
        )
    END $$ LANGUAGE SQL;

/*
 SELECT f_progress(
 '2022-06-10 10:00:00' :: TIMESTAMP,
 '2022-06-10 10:05:00' :: TIMESTAMP,
 '2022-06-10 10:10:00' :: TIMESTAMP
 )
 */