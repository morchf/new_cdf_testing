import unittest
import sys
import os

from psycopg2 import sql

from endpoints.utils.sql_builder import SqlParser, SqlFunctions

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), "..", "resources")


class TestSqlBuilder(unittest.TestCase):
    def __init__(self, *args):
        super().__init__(*args)
        self.maxDiff = sys.maxsize

    def _remove_tabs(string):
        return "".join(string.split("    "))

    """
        SqlFunctions
    """

    def test__f_percentage__lower(self):
        query = SqlParser.to_string(
            SqlFunctions.f_percentage(
                on_time_lower=5,
            )
        )

        self.assertEqual(
            query,
            """ROUND(
            (COALESCE(SUM(CASE WHEN stopendlateness < 5 THEN 1.0 END), 0) / COUNT(1))::FLOAT,
            3
        )""",
        )

    def test__f_lag(self):
        query = SqlParser.to_string(
            SqlFunctions.f_lag(
                field_name="earlypercentage",
                partition_field_names=["stopstartname", "stopendname", "direction"],
            )
        )

        self.assertEqual(
            query,
            """ARRAY(
              (LAG(ROUND(earlypercentage ::FLOAT, 3)) OVER
                (PARTITION BY stopstartname,stopendname,direction ORDER BY "period")),
                ROUND(earlypercentage ::FLOAT, 3))""",
        )

    def test__f_timeperiod(self):
        query = SqlParser.to_string(
            SqlFunctions.f_timeperiod(
                [
                    {
                        "start_time": "16:00:0",
                        "end_time": "19:00:00",
                        "label": "peak_pm",
                    },
                    {
                        "start_time": "06:00:0",
                        "end_time": "09:00:00",
                        "label": "peak_am",
                    },
                ],
                field_name="tripstarttime",
            ),
        )

        self.assertEqual(
            TestSqlBuilder._remove_tabs(query),
            TestSqlBuilder._remove_tabs(
                """
            CASE
                WHEN EXTRACT(DOW FROM tripstarttime) IN (0, 6) THEN 'weekend'
                WHEN TO_CHAR(tripstarttime, 'HH24:MI:SS')
                    BETWEEN '16:00:0' AND '19:00:00'
                    THEN 'peak_pm'
                WHEN TO_CHAR(tripstarttime, 'HH24:MI:SS')
                    BETWEEN '06:00:0' AND '09:00:00'
                    THEN 'peak_am'
                ELSE 'offpeak'
            END"""
            ),
        )

    def test__f_array_agg__basic(self):
        query = SqlParser.to_string(SqlFunctions.f_array_agg(["field1", "field2"]))

        self.assertEqual(
            query,
            """JSON_PARSE('[' || listagg('["' || field1 || '","' || field2 || '"]', ',') || ']')""",
        )

    """
        SqlParser
    """

    def test__parse__literal_and_parsed(self):
        query = SqlParser.to_string(
            SqlParser.parse(
                "SELECT * FROM {table} WHERE column = %(value)s",
                table=sql.SQL("table_name"),
                value=1,
            )
        )

        self.assertEqual(query, "SELECT * FROM table_name WHERE column = 1")

    def test__parse__extra_args(self):
        query = SqlParser.to_string(
            SqlParser.parse(
                "SELECT * FROM table WHERE column = %(value)s", value=1, value2=2
            )
        )

        self.assertEqual(query, "SELECT * FROM table WHERE column = 1")

    def test__parse__literal_for_parsed(self):
        query_call = lambda: SqlParser.parse("{table}", table="table_name")

        self.assertRaises(TypeError, query_call)

    def test__parse__array(self):
        query = SqlParser.to_string(SqlParser.parse("%(value)s", value=[1, 2, 3]))

        self.assertEqual(query, "ARRAY[1,2,3]")

    def test__parse_template(self):
        event = {
            "agency": "agency_name",
            "period": "month",
            "selected_direction": ["inbound"],
            "selected_timeperiod": ["peak_am"],
            "end_date": "2021-01-15",
            "on_time_lower": -5,
            "on_time_upper": 2,
            "timeperiod": [
                {
                    "start_time": "16:00:0",
                    "end_time": "19:00:00",
                    "label": "peak_pm",
                },
                {
                    "start_time": "06:00:0",
                    "end_time": "09:00:00",
                    "label": "peak_am",
                },
            ],
        }

        query = SqlParser.to_string(
            SqlParser.parse_template(
                "athena/agg_lateness_reduction.sql",
                **event,
                f_timeperiod=SqlFunctions.f_timeperiod(
                    event["timeperiod"], "stopstarttime"
                ),
                f_percentage__early=SqlFunctions.f_percentage(
                    on_time_upper=event["on_time_upper"]
                ),
                f_percentage__on_time=SqlFunctions.f_percentage(
                    on_time_lower=event["on_time_lower"],
                    on_time_upper=event["on_time_upper"],
                ),
                f_percentage__late=SqlFunctions.f_percentage(
                    on_time_lower=event["on_time_upper"]
                ),
            )
        )

        self.assertEqual(
            TestSqlBuilder._remove_tabs(query),
            TestSqlBuilder._remove_tabs(
                """-- agg_lateness_reduction
WITH filtered AS (
  SELECT
route,
stopendlateness::FLOAT AS stopendlateness
  FROM
public.lateness_source_data
  WHERE
agency = 'agency_name'
AND "date" BETWEEN f_period('month', '2021-01-15')
AND '2021-01-15'
AND direction = ANY(ARRAY['inbound'])
AND 
CASE
WHEN EXTRACT(DOW FROM stopstarttime) IN (0, 6) THEN 'weekend'
WHEN TO_CHAR(stopstarttime, 'HH24:MI:SS')
BETWEEN '16:00:0' AND '19:00:00'
THEN 'peak_pm'
WHEN TO_CHAR(stopstarttime, 'HH24:MI:SS')
BETWEEN '06:00:0' AND '09:00:00'
THEN 'peak_am'
ELSE 'offpeak'
END = ANY(ARRAY['peak_am'])
)
SELECT
  route,
  ROUND(AVG(stopendlateness), 3) AS avgscheduledeviation,
  ROUND(
(COALESCE(SUM(CASE WHEN stopendlateness > 2 THEN 1.0 END), 0) / COUNT(1))::FLOAT,
3
) AS earlypercentage,
  ROUND(
(COALESCE(SUM(CASE WHEN stopendlateness BETWEEN  -5 AND 2 THEN 1.0 END), 0) / COUNT(1))::FLOAT,
3
) AS ontimepercentage,
  ROUND(
(COALESCE(SUM(CASE WHEN stopendlateness < 2 THEN 1.0 END), 0) / COUNT(1))::FLOAT,
3
) AS latepercentage
FROM
  filtered
GROUP BY
  route"""
            ),
        )

    def test__combine(self):
        by_agency_query = SqlParser.parse("agency = %(agency)s", agency="agency_name")
        by_direction_query = SqlParser.parse(
            "direction = ANY(%(directions)s)", directions=[]
        )

        query = SqlParser.to_string(
            SqlParser.combine(by_agency_query, by_direction_query)
        )

        self.assertEqual(query, "agency = 'agency_name' AND direction = ANY('{}')")

    def test__combine__timeperiod(self):
        start_date = "2021-01-01"
        end_date = "2021-01-02"

        query = SqlParser.combine(
            SqlParser.parse(
                """agency = %(agency)s
            AND "date"
                BETWEEN %(start_date)s
                AND %(end_date)s
            AND direction = ANY(%(directions)s)
            """,
                agency="agency_name",
                directions=["inbound", "outbound"],
                start_date=start_date,
                end_date=end_date,
            ),
            SqlParser.parse(
                "{f_timeperiod} = ANY(%(timeperiods)s)",
                f_timeperiod=SqlFunctions.f_timeperiod(
                    [
                        {
                            "start_time": "16:00:0",
                            "end_time": "19:00:00",
                            "label": "peak_pm",
                        },
                        {
                            "start_time": "06:00:0",
                            "end_time": "09:00:00",
                            "label": "peak_am",
                        },
                    ],
                    field_name="tripstarttime",
                ),
                timeperiods=["peak_am", "offpeak"],
            ),
            separator="AND",
        )

        self.assertEqual(
            TestSqlBuilder._remove_tabs(SqlParser.to_string(query)),
            TestSqlBuilder._remove_tabs(
                """agency = 'agency_name'
AND "date"
BETWEEN '2021-01-01'
AND '2021-01-02'
AND direction = ANY(ARRAY['inbound','outbound'])
AND
CASE
WHEN EXTRACT(DOW FROM tripstarttime) IN (0, 6) THEN 'weekend'
WHEN TO_CHAR(tripstarttime, 'HH24:MI:SS')
BETWEEN '16:00:0' AND '19:00:00'
THEN 'peak_pm'
WHEN TO_CHAR(tripstarttime, 'HH24:MI:SS')
BETWEEN '06:00:0' AND '09:00:00'
THEN 'peak_am'
ELSE 'offpeak'
END = ANY(ARRAY['peak_am','offpeak'])"""
            ),
        )

    def test__parse__routes_map_data(self):
        event = {
            "agency": "sfmta",
            "route": "22",
            "period": "month",
            "selected_direction": ["inbound"],
            "selected_timeperiod": ["peak_am"],
            "start_date": "2021-08-01",
            "end_date": "2021-09-05",
            "on_time_lower": -5,
            "on_time_upper": 2,
            "timeperiod": [
                {
                    "start_time": "16:00:0",
                    "end_time": "19:00:00",
                    "label": "peak_pm",
                },
                {
                    "start_time": "06:00:0",
                    "end_time": "09:00:00",
                    "label": "peak_am",
                },
            ],
        }

        query = SqlParser.to_string(
            SqlParser.parse_template(
                "athena/routes_map_data.sql",
                **event,
                f_array_agg__shapes=SqlFunctions.f_array_agg(
                    ["shape_pt_sequence", "shape_pt_lat", "shape_pt_lon"]
                ),
                f_array_agg__stops=SqlFunctions.f_array_agg(
                    ["stop_sequence", "stop_name", "stop_lat", "stop_lon", "stop_id"]
                ),
            )
        )

        open(f"{TESTDATA_DIR}/sql_builder__routes_map_data.sql", "w").write(query)
        with open(f"{TESTDATA_DIR}/sql_builder__routes_map_data.sql") as parsed:
            self.assertEqual(query, parsed.read())


if __name__ == "__main__":
    unittest.main()
