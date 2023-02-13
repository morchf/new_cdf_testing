# ClientAPI / spark

## Getting Started

1. Install Docker
2. Run `docker-compose up` to run a Docker container with Jupyter Notebooks and Docker running. Access on http://localhost:8888

### Downloading Data

Copy data from S3 bucket to local 'data' folder for the specified date

```sh
aws s3 cp s3://backup-gtt-etl-data-dev/ ./data \
    --recursive \
    --exclude "*" \
    --include "*date_ran=2021-09-02/\*"
```
