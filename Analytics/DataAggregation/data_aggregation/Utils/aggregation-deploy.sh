# Build the docker image. Run this from inside the /Docker file where Dockerfile is present, else use `-f {relative path to Dockerfile}` as the flag
docker build -t 083011521439.dkr.ecr.us-east-1.amazonaws.com/gtt/data_aggregation .

# Tag the built Docker Image as the latest one
docker tag data_aggregation 083011521439.dkr.ecr.us-east-1.amazonaws.com/gtt/data_aggregation:hardware

# aws ecr get-login-password --region us-east-1 --profile default |  docker login --username AWS --password-stdin 083011521439.dkr.ecr.us-east-1.amazonaws.com/data_aggregation 
docker push 083011521439.dkr.ecr.us-east-1.amazonaws.com/gtt/data_aggregation:hardware

# Force new deployment
aws ecs update-service --cluster dev_data_aggregation_cluster --task-definition DataAggregation-DevTest --force-new-deployment

# ! Connect to running container - To be Edited for Data Aggregation
# aws ecs execute-command --cluster dev_data_aggregation_cluster --task arn:aws:ecs:us-east-1:083011521439:task/tsp-gtfs-realtime-cdta-Cluster/cd4c0289de4d4490a6923faf14020051 --container tsp-gtfs-realtime-cdta-DataAggregator --command "/bin/bash" --interactive

