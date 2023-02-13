import logging
import time
from typing import Dict, Optional

from sqlalchemy.sql import text


class SqlClient:
    @classmethod
    def parse(
        cls,
        query: str,
        **kwargs: Dict[str, str],
    ):
        logging.debug(query.format(**kwargs))
        return query.format(**kwargs)

    def execute(self):
        raise NotImplementedError()


class AuroraClient(SqlClient):
    """Aurora query client"""

    def __init__(self, engine):
        self._engine = engine

    def execute(self, query: str, **kwargs: Dict[str, str]):
        with self._engine.connect() as con:
            result = con.execute(text(SqlClient.parse(query, **kwargs)))

            if not result:
                raise Exception("Not found")

            return [row._asdict() for row in result]


class AthenaClient(SqlClient):
    """Athena query client"""

    def __init__(
        self, athena, *, output_location: str, workgroup: Optional[str] = "primary"
    ):
        self._athena = athena
        self._output_location = output_location
        self._workgroup = workgroup

    def execute(self, query: str, **kwargs: Dict[str, str]):
        query_execution_id = self._athena.start_query_execution(
            QueryString=SqlClient.parse(query, **kwargs),
            ResultConfiguration={"OutputLocation": self._output_location},
            WorkGroup=self._workgroup,
        ).get("QueryExecutionId")

        if query_execution_id is None:
            raise Exception("Error starting Athena query")

        while True:
            time.sleep(0.25)
            state = self._athena.get_query_execution(
                QueryExecutionId=query_execution_id
            )["QueryExecution"]["Status"]["State"]

            if state in ["FAILED", "SUCCEEDED"]:
                break

        try:
            query_results = self._athena.get_query_results(
                QueryExecutionId=query_execution_id
            )
        except Exception as e:
            raise Exception(f"Query failed: {str(e)}")

        return_query_result = []

        while True:
            header = [
                data["VarCharValue"]
                for data in query_results["ResultSet"]["Rows"][0]["Data"]
            ]
            return_query_result += [
                {
                    header[i]: data.get("VarCharValue")
                    for i, data in enumerate(row["Data"])
                }
                for row in query_results["ResultSet"]["Rows"][1:]
            ]
            if not ("NextToken" in query_results):
                break
            query_results = self._athena.get_query_results(
                NextToken=query_results["NextToken"],
                QueryExecutionId=query_execution_id,
            )

        return return_query_result
