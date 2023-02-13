# ClientAPI / api

## Getting Started

### Writing SQL

SQL queries are written for and executed by the [psycopg2](https://www.psycopg.org/docs/) library.

See [sql_builder.py](endpoints/utils/sql_builder.py) for several helper functions to safely parse SQL files with dynamic arguments

See [sql_builder.py / SqlParser](endpoints/utils/sql_builder.py) for examples on the two different placeholder substitution types in psycopg2

_Example:_

Given the below template, we can substitute the placeholders for values using psycopg2

```sql
SELECT *
FROM {table}
WHERE column1 = %(placeholder1)s -- SQL-safe value conversion
    AND column2 = {transformed_column}
```

```py
psycopg2.sql.SQL(SQL_SCRIPT).format(
    table=sql.SQL('table_name'),
    placeholder1='column_value',
    transformed_column=sql.SQL('ROUND(colum2, 3)')
)
```

In the above example, `table` and `transformed_column` use the `{}` syntax and are open to SQL injection attacks. Do not directly expose these placeholders to user-input.

For reusable SQL snippets, [sql_builder.py / SqlFunctions](endpoints/utils/sql_builder.py) has several functions converting user-input to dynamic SQL statements. User-controlled values are _always_ substituted using the `%()s` syntax, which parses raw Python values to SQL-safe interpretations

### Running Tests

```sh
python -m unittest
```

_Must be running Python 3.x_

To connect the VS Code test runner, add the following line to your workspace `settings.json`

```json
"python.testing.unittestArgs": [
    "-v",
    "-s",
    "./ClientAPI/api",
    "-p",
    "test*.py"
],
```

### Formatting SQL Files

The [SQL Formatter](https://marketplace.visualstudio.com/items?itemName=adpyke.vscode-sql-formatter) extension in VS Code handles SQL formatting the best, though it does not properly handle placeholders and `$$` in Redshift stored procedures
