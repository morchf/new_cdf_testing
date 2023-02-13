# ClientAPI / airflow

The 'airflow' directory contains the code for provisioning and running DAGs used by the Client API.

## Getting Started

When developing DAGs, it may be helpful to run an Airflow instance locally. The structure of the 'airflow' folder aligns with the structure needed to deploy an Airflow instance. Run the below commands to clone the Docker Compose file used to provision a local Airflow instance

```bash
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.2.3/docker-compose.yaml'
docker-compose up
```

The running instance can be reached at http://localhost:8080 with the below credentials:

- Username: airflow
- Password: airflow

## Connecting to AWS

Run to sync entire airflow directory with AWS. Set the proper `ENV` variable to the environment before use (dev/qa/prod)

```sh
chmod +x config/sync.sh
export AWS_PROFILE=dev

./synch.sh
```
