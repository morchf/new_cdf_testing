to run on ssh ec2:
- docker build . -t "vps-stat"
- docker run -it --rm --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock --network="host" vps-stat 
- can run with additional arguments (check --help)