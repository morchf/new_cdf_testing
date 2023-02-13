import json
from typing import Dict, List

from airflow.hooks.base_hook import BaseHook
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from common.common import evaluate, items
from services.sql import AthenaService, PostgresService


def format_partitions(partitions: Dict[str, str], as_array=True) -> str:
    """
    Convert a partition dictionary to a tring in one of two formats:

    1. JSON dictionary { "k": ["v"] } -> '{ "k": ["v"] }'
    2. Key-value array: { "k": ["v"] } -> [ ['k', ['v']] ]
    """
    parsed_partitions = dict(zip(partitions, map(evaluate, partitions.values())))

    if not as_array:
        return json.dumps(parsed_partitions)
    return json.dumps(items(parsed_partitions))


class BaseDwhService:
    """
    Base processes for syncing raw data with DWH
    """

    TASK_GROUP_ID = "dwh"

    def __init__(
        self,
        conn_id: str,
        partitions: Dict[str, str],
        athena_conn_id: str = "athena_default",
    ):
        self.conn_id = conn_id

        # Services
        self.postgres_service = PostgresService(conn_id=conn_id)

        athena_conn = BaseHook.get_connection(athena_conn_id)
        athena_conn_details = json.loads(athena_conn.get_extra())

        self.athena_service = AthenaService(
            output_location=athena_conn_details.get("output_location"),
            workgroup=athena_conn_details.get("workgroup", "primary"),
        )

        self.partitions = partitions

    @property
    def partition_args(self):
        return (
            "{{ ti.xcom_pull(task_ids='" + self.TASK_GROUP_ID + "__partition_args') }}"
        )

    @property
    def partition_kwargs(self):
        return (
            "{{ ti.xcom_pull(task_ids='"
            + self.TASK_GROUP_ID
            + "__partition_kwargs') }}"
        )

    def prepare(self, **kwargs):
        """
        Run pre-tasks
        """
        with TaskGroup(
            group_id=f"{self.TASK_GROUP_ID}__format_partitions",
            prefix_group_id=False,
        ) as format_sql_args:
            PythonOperator(
                task_id=f"{self.TASK_GROUP_ID}__partition_args",
                python_callable=format_partitions,
                op_kwargs={"partitions": self.partitions, "as_array": True},
                **kwargs,
            )

            PythonOperator(
                task_id=f"{self.TASK_GROUP_ID}__partition_kwargs",
                python_callable=format_partitions,
                op_kwargs={"partitions": self.partitions, "as_array": False},
                **kwargs,
            )

        return format_sql_args

    def copy_table(self, table: object, **kwargs):
        return self.postgres_service.call_procedure(
            task_id=f"copy__{table['table']}",
            procedure_name="sp_copy_external",
            procedure_args="""(
                '{{{{ params.external_table }}}}',
                '{{{{ params.table }}}}',
                JSON_PARSE('{partition_args}')
            )""".format(
                partition_args=self.partition_args
            ),
            params={
                "external_table": f"{table['external_schema']}.{table['table']}",
                "table": f"{table['schema']}.{table['table']}",
            },
            **kwargs,
        )

    def update_partitions(self, table: object, **kwargs):
        return self.athena_service.execute(
            task_id=f"update_partitions__{table['table']}",
            query=f"MSCK REPAIR TABLE {table['table']}",
            database=table["external_db"],
            **kwargs,
        )

    def sync_tables(
        self,
        tables: List[object],
        refresh_procedure_name: str = None,
        refresh_procedure_args: Dict[str, str] = None,
        **kwargs,
    ):
        """
        Load raw data and refresh tables
        """

        with TaskGroup(
            group_id=f"{self.TASK_GROUP_ID}__sync_tables",
            prefix_group_id=False,
        ) as sync_tables:
            sync_tasks = []

            for table in tables:
                copy_table, update_partitions = None, None

                # Remove existing values and copy over new ones
                # Copy/replace existing values if table synced to DWH
                if (
                    "external_schema" in table
                    and "schema" in table
                    and "table" in table
                ):
                    copy_table = self.copy_table(table)

                # Update Athena partitions
                # Manually update partitions,
                if "external_db" in table and "table" in table:
                    update_partitions = self.update_partitions(table)

                if copy_table is not None and update_partitions is not None:
                    update_partitions >> copy_table
                    sync_tasks.append(copy_table)
                elif copy_table is not None:
                    sync_tasks.append(copy_table)
                elif update_partitions is not None:
                    sync_tasks.append(update_partitions)

            if refresh_procedure_name is not None:
                refresh = self.postgres_service.call_procedure(
                    procedure_name=refresh_procedure_name,
                    procedure_args=refresh_procedure_args,
                    **kwargs,
                )

                sync_tasks >> refresh

        return sync_tables

    def update_config(self, id_column: str, values: str, **kwargs):
        """
        Update any agency configuration in DWH
        """
        delete_agency_config = self.postgres_service.execute(
            task_id=f"{self.TASK_GROUP_ID}__delete_agency_config",
            sql=f"""
            DELETE FROM cfg_agency
            WHERE {id_column} ='{values[id_column]}'
            """,
        )

        update_agency_config = self.postgres_service.execute(
            task_id=f"{self.TASK_GROUP_ID}__update_agency_config",
            sql=f"""
            INSERT INTO cfg_agency ({','.join(values.keys())})
            VALUES ({','.join(map(lambda x: "'" + x + "'", values.values()))})
            """,
        )

        delete_agency_config >> update_agency_config

        return update_agency_config


class StaticGtfsDwhService(BaseDwhService):
    """
    Sync and process static GTFS
    """

    TASK_GROUP_ID = "static-gtfs-dwh"

    def sync_tables(self, tables: List[object], **kwargs):
        return super().sync_tables(
            tables=tables, refresh_procedure_name="sp_refresh_gtfs"
        )


class IntersectionsDwhService(BaseDwhService):
    """
    Sync and process static intersections
    """

    TASK_GROUP_ID = "static-intersections-dwh"


class MetricsDwhService(BaseDwhService):
    def __init__(self, agency: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.agency = agency

    def load_travel_time(self, procedure_name: str, **kwargs):
        """
        Create travel time metrics from TSP dataset tables
        """
        with TaskGroup(
            group_id=f"{self.TASK_GROUP_ID}__parse_vehicle_logs",
            prefix_group_id=False,
        ) as load_travel_time:
            parse_vehicle_logs = self.postgres_service.call_procedure(
                procedure_name="sp_parse_vehicle_logs",
                procedure_args="""(
                    '{{{{ params.procedure_name }}}}',
                    JSON_PARSE('{partition_kwargs}')
                )""".format(
                    partition_kwargs=self.partition_kwargs
                ),
                params={"procedure_name": procedure_name},
                **kwargs,
            )

            refresh_travel_time = self.postgres_service.call_procedure(
                procedure_name="sp_refresh_travel_time",
            )

            parse_vehicle_logs >> refresh_travel_time

        return load_travel_time


class CvpDwhService(MetricsDwhService):
    """
    Sync and process data for CVP
    """

    TASK_GROUP_ID = "cvp-dwh"

    def sync_tables(self, tables: List[object], **kwargs):
        """
        Sync DWH tables with CVP logs
        """

        return super().sync_tables(
            tables=tables,
            refresh_procedure_name="sp_refresh_tsp__cvp",
            refresh_procedure_args=f"('{self.agency}')",
        )

    def load_travel_time(self, **kwargs):
        """
        Use CVP logs to build metrics tables

        Refresh metrics table views
        """
        return super().load_travel_time(
            procedure_name="sp_parse_vehicle_logs__cvp", **kwargs
        )


class RtRadioDwhService(BaseDwhService):
    """
    Sync data for RT Radio messages
    """

    TASK_GROUP_ID = "rt-radio-dwh"

    def __init__(self, agency: str, agency_id: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.agency = agency
        self.agency_id = agency_id

    def sync_tables(self, tables: List[object], local_timezone: str, **kwargs):
        """
        Sync DWH tables with RT GTFS and GPS logs
        """
        with TaskGroup(
            group_id=f"{self.TASK_GROUP_ID}__sync",
            prefix_group_id=False,
        ) as sync:
            # TODO: Convert agency_id references from agency short-name to GUID
            super().update_config(
                id_column="agency_id",
                values={
                    "agency_id": self.agency_id,
                    "agency": self.agency,
                    "local_timezone": local_timezone,
                },
            )
            super().sync_tables(tables=tables)

        return sync


class RtGtfsDwhService(MetricsDwhService):
    """
    Sync and process data for RT GTFS
    """

    TASK_GROUP_ID = "rt-gtfs-dwh"

    def sync_tables(self, tables: List[object], **kwargs):
        """
        Sync DWH tables with RT GTFS and GPS logs
        """
        return super().sync_tables(
            tables=tables,
            refresh_procedure_name="sp_refresh_tsp__rt_gtfs",
            refresh_procedure_args=f"('{self.agency}')",
        )

    def load_travel_time(self, **kwargs):
        """
        Use RT GTFS and GPS logs to build metrics tables
        """

        return super().load_travel_time(
            procedure_name="sp_parse_vehicle_logs__rt_gtfs", **kwargs
        )


class Mp70DwhService(BaseDwhService):
    """
    Synch and process data for MP70
    """

    TASK_GROUP_ID = "mp70"

    def __init__(self, region: str, agency: str, agency_id: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.region = region
        self.agency = agency
        self.agency_id = agency_id

    def sync_tables(self, tables: List[object], **kwargs):
        """
        Synchronize DWH tables with MP70
        """
        """
        Sync DWH tables with RT GTFS and GPS logs
        """
        with TaskGroup(
            group_id=f"{self.TASK_GROUP_ID}__sync",
            prefix_group_id=False,
        ) as sync:
            # TODO: Convert agency_id references from agency short-name to GUID
            self.update_config(
                id_column="agency_id",
                values={"agency_id": self.agency_id, "agency": self.agency},
            )

            super().sync_tables(
                tables=tables,
                refresh_procedure_name="sp_refresh_tables__evp",
                refresh_procedure_args=f"('{self.agency}','{self.agency_id}')",
            )

        return sync


class EvpDwhService(BaseDwhService):
    """
    Process data for EVP metrics
    """

    TASK_GROUP_ID = "evp"

    def load_evp_metrics(self, **kwargs):
        """
        Build EVP metrics tables

        Refresh metrics table views
        """

        with TaskGroup(
            group_id=f"{BaseDwhService.TASK_GROUP_ID}__load_evp_metrics"
        ) as load_evp_metrics:
            parse_vehicle_logs = self.postgres_service.call_procedure(
                procedure_name="sp_parse_vehicle_logs",
                procedure_args="""(
                    'sp_parse_vehicle_logs__mp70',
                    JSON_PARSE('{partition_kwargs}')
                )""".format(
                    partition_kwargs=self.partition_kwargs
                ),
                **kwargs,
            )

            refresh_evp_metrics = self.postgres_service.call_procedure(
                procedure_name="sp_refresh_evp_metrics",
            )
            parse_vehicle_logs >> refresh_evp_metrics

        return load_evp_metrics
