import logging
import re
from os import listdir, path, walk
from typing import List

from core.constants import SQL_FILES


class DwhManager:
    """
    Manage DWH resources, using a 'version' script to keep track of the DWH
    version and conditionally run migration scripts
    """

    def __init__(self, postgres_client, sql_kwargs):
        self.postgres_client = postgres_client
        self.sql_kwargs = sql_kwargs

    def _extract_script_commands(self, file_name: str, contents: str) -> List[str]:
        if contents is None:
            raise Exception("Empty file")

        # Allow multiple commands per file
        # Avoids '...cannot run inside a multiple commands statement'
        # Only split non-stored procedure files (which may contain ';')
        is_procedure = re.match(r"sp_.*\.sql", file_name)
        return (
            [contents]
            if is_procedure
            else [c for c in contents.split(";") if not c == "" and not c.isspace()]
        )

    def migrate_dwh(self):
        """
        Migrate DWH to current version

        1. Check current version
        2. Run any versioning scripts greater than current DWH version
        3. Run SQL scripts in order matching constants.py
        4. Update user permissions
        5. Update DWH version
        """
        # Load all files in directory order
        sql_file_paths = []
        for directory in SQL_FILES:
            # Directly add manually defined files
            if re.match(r".*\.sql", directory):
                sql_file_paths = sql_file_paths + [directory]
                continue

            for root, _, files in walk(directory):
                new_sql_file_paths = [
                    f"{root}/{file}"
                    for file in files
                    # Skip re-adding fully-described file paths
                    if f"{root}/{file}" not in sql_file_paths
                ]
                sql_file_paths = sql_file_paths + new_sql_file_paths

        # Use current DWH version to conditionally run migration scripts
        current_dwh_version = self.execute_script("scripts/version.sql")
        current_dwh_version = (
            current_dwh_version[0].get("version", 0)
            if current_dwh_version and len(current_dwh_version) == 1
            else None
        )

        logging.info(f"Current DWH Version: {current_dwh_version}")

        if current_dwh_version:
            migration_sql_file_paths = []

            for root, _, files in walk("versions"):
                if len(files) == 0:
                    continue

                script_version = int(root.split("/")[1])

                if script_version <= current_dwh_version:
                    continue

                migration_sql_file_paths = (
                    list(map(lambda file: f"{root}/{file}", files))
                    + migration_sql_file_paths
                )

            # Execute migration scripts before any others
            sql_file_paths = migration_sql_file_paths + sql_file_paths

        # Execute each of the files
        for sql_file_path in sql_file_paths:
            self.execute_script(sql_file_path)

    def execute(self, sql):
        """
        Run a single SQL command with kwargs
        """
        return self.postgres_client.execute(sql, sql_kwargs=self.sql_kwargs)

    def execute_script(self, sql_file_path):
        """
        Execute a SQL script file, converting non-stored procedures to multiple
        commands by splitting on ';'
        """

        # Verify in new transaction state
        self.postgres_client.rollback()

        logging.info("Executing file: %s" % sql_file_path)

        with open(sql_file_path, encoding="utf8") as sql_file:
            contents = sql_file.read()

            commands = self._extract_script_commands(
                path.basename(sql_file.name), contents
            )

            if len(commands) == 0:
                return

            results = []
            for command in commands:
                try:
                    results.append(self.execute(command))
                except Exception as exception:
                    self.postgres_client.rollback()
                    logging.error(exception)

            # Assume file has 1 command
            if len(results) == 1:
                return results[-1]

            return results

    def test(self):
        """
        Run included test-suite. Must run after migration
        """
        logging.info("Running tests")

        tests = [
            test_procedure.replace(".sql", "")
            for test_procedure in listdir("test/specs")
            if re.match(r"sp_test__.*\.sql", path.basename(test_procedure))
        ]

        for (i, test) in enumerate(tests):
            logging.info(f"Running test {test} [{i + 1}/{len(tests)}]")
            result = self.postgres_client.execute(
                f"CALL testing.{test}()", sql_kwargs=self.sql_kwargs
            )
            logging.info(result)
