# Deployment / StaticGtfsPoller

## Getting Started

Run from the project root. Make sure `AWS_ACCOUNT` and `AWS_REGION` are specified in your shell environment

```sh
AWS_ACCOUNT=<account id> \
AWS_REGION=<region> \
docker-compose \
    -f Deployment/TSPPipeline/Tasks/StaticGtfsPoller/docker-compose.yml \
    up --build
```
