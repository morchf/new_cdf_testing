# TSP In Cloud Deployment

This CDK project is designed to deploy a growing number of Fargate services with as little mess and duplication as possible. What would be thousands of lines of CloudFormation YAML can be represented in less than one hundred lines of CDK, due to the usual benefits of programming abstractions such as functions, classes, and string manipulation.

## Adding a Service

1. To add a new Fargate service to the deployment, edit `services.py`. Here you'll see several other Fargate services defined as simple function calls. The type hints and inline python docs should be more than self-explanatory.

2. In addition to creating the service in CDK, you'll need to add a `{service_name}-requirements.txt` under `Deployment/TSPPipeline/Docker` in order for the Docker build to succeed for your service. If your service has no extra requirements outside those listed in `Deployment/TSPPipeline/Docker/core-requirements.txt`, simply add a blank file.

> \*Note that `{service_name}` must be the same as the name of the python file, ex. If your service is at `TSP/tsp-gtfs-realtime/tsp_gtfs_realtime/agency_manager.py` then your requirements file must be at `Deployment/TSPPipeline/Docker/agency_manager-requirements.txt`

3. Finally, you'll need to add your `{service_name}` to the list of `services` in `TSPBuildspec.yml`.

## How it works

CDK comes with its own set of CLI tools called the 'CDK toolkit'. The most useful of which are:

```sh
cdk bootstrap # Prepares the project for deployment
```

```sh
cdk synth # 'Synthesizes' a CFN template from the code
```

```sh
cdk deploy # Creates and deploys a CloudFormation changeset/stack
```

We use all three of these in `TSPBuildspec.yml`

### Entrypoint

The 'entrypoint' of the CDK application is at `app.py`. Here you'll see the `TSPInCloudStack` class defined, where it instantiates a VPC and the other various high level 'constructs' associated with the stack.

### Constructs

A `Construct` in CDK is sort of equivalent to a CloudFormation resource, except that with CDK, you can make your own logical Constructs whose only purpose is to encapsulate other Constructs. Hence the many places throughout this code base where we inheret from `Construct`.
