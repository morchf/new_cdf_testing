# TSP GTFS Realtime
This library contains prototype code for using a GTFS Realtime feed provided by an agency. There are also example services that can be run using Docker. While the design is meant to point to aws endpoints, development and testing has only been done locally.

The `gtfs_realtime_api_poller` service connects to the GTFS Realtime feed URLs, polls periodically, and persists the data in an elasticache (redis) instance. It then send an update message that subscribers can use to know about relevant new data. More information can be found in the [gtfs_realtime package](tsp_gtfs_realtime/gtfs_realtime/readme.md)

The `agency_manager` service waits for any new vehicle data, then it launches a new `vehicle_manager` service for each vehicle that is not currently being managed. It likely will change to trips instead of vehicles. It currently requires querying the docker engine to get the current list of running and stopped containers, but there are likely better ways to monitor running instances. More information can be found in the [core package](tsp_gtfs_realtime/core/readme.md)

The `vehicle_manager` service waits for new vehicle data about a particular vehicle, then gets the data from the elasticache instance. It can run for a specified number of sample or until it times out. It has some basic functionality like printing the data or basic statistics.

The `route_manager` service waits for new trip data about a particular route, then gets the trip and vehicle data from the elasticache instance. It can run for a specified number of sample or until it times out. It has some basic functionality like printing the data or basic statistics.

# Usage
To run the services using locally hosted `redis` with docker-compose
```
docker-compose up
```
will build the image specified by the Dockerfile and create containers for a local `redis` instance, as well as the `gtfs_realtime_api_poller` and `agency_manager` services. The `agency_manager` will spawn containers to handle each vehicle.

docker-compose.yml is currently designed to be started locally to aid development. The local folder is mounted as a bind mount which allows for modifying files on the host machine, then restarting a service (to load a different agency config file, for example)

## Manually connecting to local services
The docker-compose `redis` service binds the redis-server to 0.0.0.0 and exposes port 6379 to the host. This allows the access to the redis instance either at localhost:6379 from the host machine or redis:6379 from a docker container that is on the same docker network as the other docker-compose project services. This means you can debug in the following ways after starting the other services with `docker-compose up -d`:

example debugging on host, attaching pdb to debug exceptions
```
vid=1800

python -m pdb -c continue tsp_gtfs_realtime/vehicle_manager.py \
  --get-update-frequency \
  --vehicle-id $vid \
  --num-samples 10 \
  --timeout 120
```

example debugging in container
```
vid=1800
image_name=vehicle-manager
container_name=${image_name}_${vid}

docker build -t $image_name .

# run some file to test in a new container in the same network as the docker-compose
# project, with a psuedo-tty shell allocated, and remove once done
docker run \
  --rm \
  -e REDIS_URL=redis \
  -e REDIS_PORT=6379 \
  --network tsp-gtfs-realtime_default \
  -v "$(pwd)":/root/tsp-gtfs-realtime \
  --name $container_name \
  $image_name \
  python /root/tsp-gtfs-realtime/tsp_gtfs_realtime/vehicle_manager.py \
    --get-update-frequency \
    --vehicle-id $vid \
    --num-samples 10 \
    --timeout 120
```

## Data Pipeline
Elasticache is used to persist all relevant data, and services don't directly pass any data between themselves. Instead, the redis pubsub feature is used to publish messages about the data so that that any subscriber can know when there is new data available. A pubsub message consists of a channel and a message. The following channels are the only ones currently used, but this can be extended

- new_vehicle_position:*vehicle_id*, *vehicle_id*
- new_agency_data, *timestamp*

The colon to represent nested information is a redis convention, and it is easy to use wildcards and patterns to subscribe to a channel by doing `new_vehicle_position:*`, for example to get every vehicle_id. This makes it a bit redundant that the id is published in the message field, but this can be refined as required. The actual agency_id is also not currently published. This assumes the elasticache instance will only be available to services belonging to the same agency.

# Install with pip
Development (editable with development and jupyter notebook packages installed)
```
pip install -e '.[all]'
```

Production
```
pip install .
```

Installing with `pip` and `setuptools` is nice for development and distribution of code, but for running in a production container, it will likely make more sense to just use a number of `requirements.txt` files.

# Deployment
Deployment is a multi-step process since there are resources that are shared between all agencies and services using this solution, and agencies that belong only to a specific agency.
## Core
Eventually, there will be more service connections between TSP and SCP, but currently the networking layer and shared resources are deployed with the "Deployment/TSPCoreDeployCFN.yml" template

This optionally creates a bastion server, which will enable communication to aws resources for debugging and development. This requires running the `Deployment/pre-deploy-core.sh` helper script, which will create a public/private key pair that will be  required to SSH into the bastion server. This key can be later deleted by adding the `-d` flag

Usage:
```
./Deployment/pre-deploy-core.sh -h
-k [key_pair_name]  Name for SSH KeyPair to be created. Default=TSPBastionKey
                    Private Key will be saved to [key_pair_name].pem
-d                  Delete resources
```

Example deployment:
```
./Deployment/pre-deploy-core.sh
aws cloudformation create-stack \
  --stack-name tsp-gtfs-realtime \
  --template-body file://Deployment/TSPCoreDeployCFN.yml \
  --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM \
  --parameters \
    ParameterKey=CreateBastionServer,ParameterValue=true \
    ParameterKey=BastionServerSSHKeyPairName,ParameterValue='TSPBastionKey'
```
The tsp-gtfs-realtime stack can then be found at https://console.aws.amazon.com/cloudformation/home

To delete the cloud resources, the stack can be deleted with
```
aws cloudformation delete-stack --stack-name tsp-gtfs-realtime
```
## Agency
A similar process will deploy an agency that will use these resources. This process should be refined to automate the building of the docker images to ECR, the configuration connection to an agency within CDF, and any required scaling. But an initial deployment example is below, which only deploys the `gtfs-realtime-api-poller` service, which populated the elasticache cluster for an agency.

It should be noted that the built docker image contains the example config file, so currently only the "Duluth Transit" agency can (easily) be run. This can be expanded to add functionality around current process or to add the CDF process connection. The docker process needs to be refined to create the minimal images for each function as well, which require further refinement of the library and modules.

Example Deployment:
```
./Deployment/pre-deploy-agency.sh
aws cloudformation create-stack \
  --stack-name tsp-gtfs-realtime-duluth-transit \
  --template-body file://Deployment/TSPAgencyDeployCFN.yml \
  --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM \
  --parameters \
    ParameterKey=TSPCoreStack,ParameterValue=tsp-gtfs-realtime \
    ParameterKey=AgencyId,ParameterValue=duluth-transit \
    ParameterKey=ImageUri,ParameterValue=083011521439.dkr.ecr.us-east-2.amazonaws.com/gtt/tsp-gtfs-realtime:latest
```

# Deployment Questions
## AWS
While this was designed to point to aws services, it was all developed locally. For the elasticache instance, this will likely just require changing the authentication process and url, but there also should be a CloudFormation template for provisioning the necessary resources for an agency and a way to persist the access and configuration data.

## Docker
There are a number of things that can be improved around Docker, but it likely depends on how the aws fargate deployment process affects the best way to programmatically configure and spawn new containers for each vehicle (or trip). It likely will make sense to have minimal docker images that only contain the necessary libraries for each service. Currently, this is not done, and there is one base image that is shared between all the services. Creating these minimal images is often done by creating a "build" image that installs the dependencies with pip then copies them to the "slim" version of the python image for production. These images can be packaged and managed using AWS Elastic Container Registry, and each service type can already have its own prebuilt image.

When launching services with docker-compose, it groups them into a single "project" and automatically manages shared resources. This is great, but requires knowing all of the running containers before starting the fargate task. Using the static GTFS data, it might be possible to know all of the scheduled trips and then just restart containers on a schedule. In the current approach, where new vehicle managers are started with a vehicle_id configured at runtime, the containers are not part of the docker-compose project. While tools like docker swarm and Kubernetes exist to handle multiple instances of a container, it does not seem like the same process should be used when all of the instances are configured differently. This needs to be investigated in Fargate to determine the best way to have thousands of similar containers.

Beyond launching, health monitoring and gracefully dying are also important. The static GTFS data can give expectations for how long a container should run, and it would be worth finding out whether this can be solely relied upon to know when a container should be running. On the other end of the spectrum is the current approach which simply watches for new vehicles that do not have a manager then spawn a container that runs until it times out. This is simpler to manage, but it might have additional overhead due to querying currently running containers. Alternatively, through CloudWatch or maybe just Fargate itself, it might be possible to specifically handle a container when it dies.

## GTFS Realtime data
One important point about GTFS Realtime data is that it's only a specification and most fields are optional. This means that we can either place restrictions beyond the specification for things that we require, or that we need multiple ways to perform a calculation based on what fields are populated. Ideally, this would not require any agency-level configuration differences, and an agency service would run as long as there is any GTFS Realtime feed. Beyond which fields are used, there will almost certainly be small differences across agencies, and capturing quality metrics will help mitigate the issues that arise. There will be many strategies for dealing with these differences, so this will be an ongoing thing to keep in mind throughout development.

## Location and workflow within SCP
Moving this codebase to the SCP repo will require unification of development and deployment processes.

- folder structure
- shared code/classes?
- aws sam packaging/deployment
- cloudformation template and division of resources
- unit testing. remote/automatic?
- avoiding pip?
