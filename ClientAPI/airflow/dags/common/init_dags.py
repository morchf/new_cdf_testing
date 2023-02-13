import logging
from typing import List, Tuple

from airflow import DAG
from airflow.models import Variable

LOGGER = logging.getLogger(__name__)


def get_dags_to_load(factory) -> List[Tuple[str, DAG]]:
    """
    Return list of (dag_id, dag) pairs to load.
    For every agency, get list of dags to load.
    Create a DAG instance, if the provided factory object can do that.
    """
    agencies = Variable.get("agencies_list", deserialize_json=True)
    result = []

    LOGGER.info(f"Loading dags for {factory.get_name()}")
    LOGGER.info(f"List of agencies: {agencies}")

    for agency in agencies:
        config = Variable.get(f"{agency}_config", deserialize_json=True)
        dags_to_create = config.get("dags", {})
        if dags_to_create and factory.get_name() in dags_to_create:
            result.append(factory(agency))

    LOGGER.info(f"Loading dags: {[t[0] for t in result]}")  # log dag_id
    return result
