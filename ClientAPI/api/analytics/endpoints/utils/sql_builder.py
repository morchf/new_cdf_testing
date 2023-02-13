import pathlib
from typing import Dict, Iterable, List, Union
from psycopg2 import sql
from psycopg2.extensions import cursor


class Cursor(cursor):
    """
    Use psycopg2 'static' methods
    """

    def __init__(self, *args, **kwargs):
        pass


parsing_cursor = Cursor()


class SqlParser:
    """
    Parse psycopg2 SQL expressions.
    See: https://www.psycopg.org/docs

    Parameterized queries accept values in two forms:

    {placeholder} : `{}` Curly-braced placeholders

    These are used to directly substitute strings, such as table names or for
    reusable SQL snippets. These do not accept literal strings and instead
    must be wrapped by `psycopg2.sql.SQL` or another psycopg2 SQL type
    See: https://www.psycopg.org/docs/sql.html

    %(placeholder)s : `%()s` Value placeholders

    These are used to parse Python variables to a SQL equivalent. Strings are
    wrapped in `''` and arrays are converted to `ARRAY['value1','value2']`

    """

    def parse(
        query: Union[str, sql.SQL],
        *args: List[Union[str, sql.SQL]],
        **kwargs: Dict[str, Union[str, sql.SQL]],
    ) -> sql.SQL:
        """
        Parse string or psycopg2 SQl composable with keyword/array arguments
        """
        try:
            # Substitute literal args
            literal_query = SqlParser.to_string(
                (sql.SQL(SqlParser.to_string(query))).format(**kwargs),
            )

            return sql.SQL(
                parsing_cursor.mogrify(
                    literal_query,
                    args if len(args) > 0 else kwargs,
                ).decode()
            )
        except TypeError as e:
            raise TypeError(
                "Passed literal substitution as a raw string. Wrap in a psycopg2.sql type",
                e,
            )
        except ValueError as e:
            raise ValueError("Incorrect template format. Use `%(value)s`", e)

    def parse_template(
        file_name: str,
        *args: Iterable[Union[str, sql.SQL]],
        **kwargs: Dict[str, Union[str, sql.SQL]],
    ) -> sql.SQL:
        """
        Parse file with keyword/array arguments
        """
        with (pathlib.Path(__file__) / ".." / ".." / file_name).resolve().open() as f:
            query_format = f.read()

            return SqlParser.parse(sql.SQL(query_format), *args, **kwargs)

    def to_string(composable: Union[str, sql.SQL, sql.Composable]) -> str:
        """
        Convert psycopg2 SQL statements to a string
        """
        if isinstance(composable, str):
            return composable
        elif isinstance(composable, sql.Composed):
            return "".join([SqlParser.to_string(x) for x in composable])
        elif isinstance(composable, sql.SQL):
            return composable.string
        else:
            raw = sql.ext.adapt(composable._wrapped).getquoted()
            return raw.decode() if isinstance(raw, bytes) else raw

    def combine(
        *statements: List[Union[sql.SQL, sql.Composable]], separator: str = " AND "
    ) -> sql.SQL:
        """
        Combine SQL arguments with a separator

        Args:
            statements: List of SQL statements
            separator: String to join statements

        Returns: SQL statement joined by the separator string
        """
        return sql.SQL(separator).join(statements)


class SqlFunctions:
    """
    SQL functions using parsed SQL templates

    NOTE: Functions to be replaced by table functions. Not supported in Redshift
    """

    def f_percentage(
        field_name: str = "stopendlateness",
        on_time_lower: int = None,
        on_time_upper: int = None,
        precision: int = 3,
    ) -> sql.SQL:
        """
        Convert field to percentage

        Args:
            field_name: Field to transform
            on_time_lower: Lower band for on-time
            on_time_upper: Upper band for on-time
            precision: Precision of return value

        Returns: Percentage of field in specified on-time band
        """

        # Build on-time filter
        if on_time_lower and on_time_upper:
            filter = sql.SQL(
                "{field_name} BETWEEN %(on_time_lower)s AND %(on_time_upper)s"
            )
        elif on_time_upper:
            filter = sql.SQL("{field_name} > %(on_time_upper)s")
        else:
            filter = sql.SQL("{field_name} < %(on_time_lower)s")

        # Filter with lower/upper limit
        filter = SqlParser.parse(
            filter.format(field_name=sql.SQL(field_name)),
            on_time_lower=on_time_lower,
            on_time_upper=on_time_upper,
        )

        return sql.SQL(
            """ROUND(
            (COALESCE(SUM(CASE WHEN {filter} THEN 1.0 END), 0) / COUNT(1))::FLOAT,
            {precision}
        )"""
        ).format(precision=sql.SQL(repr(precision)), filter=filter)

    def f_lag(
        field_name: str,
        partition_field_names: List[str] = [],
        order_by_field_name: str = '"period"',
        precision=3,
    ) -> sql.SQL:
        """
        Transform field to percentage

        Args:
            field_name: Field to transform
            partition_field_names: List of partition fields
            order_by_field_name: Field to order lagged-values

        Returns: Percentage of field in specified
        """

        partition_by = (
            sql.SQL("PARTITION BY {partition_field_names} ",).format(
                partition_field_names=sql.SQL(",").join(
                    list(map(lambda x: sql.SQL(x), partition_field_names))
                ),
            )
            if len(partition_field_names) > 0
            else sql.SQL("")
        )
        order_by = (
            sql.SQL("ORDER BY {order_by_field_name}").format(
                order_by_field_name=sql.SQL(order_by_field_name),
            )
            if len(order_by_field_name) > 0
            else sql.SQL("")
        )

        return sql.SQL(
            """ARRAY(
              (LAG(ROUND({field_name} ::FLOAT, {precision})) OVER
                ({partition_by}{order_by})),
                ROUND({field_name} ::FLOAT, {precision}))"""
        ).format(
            field_name=sql.SQL(field_name),
            precision=sql.SQL(repr(precision)),
            partition_by=partition_by,
            order_by=order_by,
        )

    def _f_timeperiod_band(
        start_time: str, end_time: str, label: str, field_name: str
    ) -> sql.SQL:
        return SqlParser.parse(
            """
                WHEN TO_CHAR({field_name}, 'HH24:MI:SS')
                    BETWEEN %(start_time)s AND %(end_time)s
                    THEN %(label)s""",
            field_name=sql.SQL(field_name),
            start_time=start_time,
            end_time=end_time,
            label=label,
        )

    def f_timeperiod(timeperiods: List, field_name="label") -> sql.SQL:
        """
        Create a case statement filter for the selected timeperiods

        Args:
            timeperiods: Definitions of the timeperiods
            selected_timeperiods: Array of matching timeperiods
            field_name: Field to matching timeperiod on

        Returns: SQL filter matching selected timeperiods
        """

        # Weekend
        weekend_case = sql.SQL(
            """
            CASE
                WHEN EXTRACT(DOW FROM {field_name}) IN (0, 6) THEN 'weekend'"""
        ).format(field_name=sql.SQL(field_name))

        # Timeperiods
        timeperiod_case = [
            SqlFunctions._f_timeperiod_band(
                timeperiod["start_time"],
                timeperiod["end_time"],
                timeperiod["label"],
                field_name,
            )
            for timeperiod in timeperiods
        ]

        # Offpeak
        offpeak_case = sql.SQL(
            """
                ELSE 'offpeak'
            END"""
        )

        return sql.Composed([weekend_case, *timeperiod_case, offpeak_case])

    def _n_elements(n: int, template: str = "%s", separator: str = ",") -> sql.SQL:
        """
        Build a SQL statement template for multiple array elements

        Args:
            n: Number of elements

        Returns: SQL statement of the template joined the separator
        """
        return sql.SQL(
            SqlParser.to_string(sql.SQL(separator).join([sql.SQL(template)] * n))
        )

    def f_array_agg(fields: List[str]):
        """
        Combines fields into an array of arrays

        Args:
            fields: Array of fields for each array element

        Return:
            Statement to combine fields into array of arrays
        """

        array = SqlFunctions._n_elements(
            len(fields), template="{}", separator=" || '\",\"' || "
        ).format(*list(map(lambda x: sql.SQL(x), fields)))

        return sql.SQL(
            "JSON_PARSE('[' || listagg('[\"' || {array} || '\"]', ',') || ']')"
        ).format(array=array)
