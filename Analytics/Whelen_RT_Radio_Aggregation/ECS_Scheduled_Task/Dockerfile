# Dockerfile, Image, container

# base image
FROM ubuntu:20.04 

# Install OpenJDK-8
RUN apt-get update && \
    apt-get install -y openjdk-8-jdk && \
    apt-get install python3.8 -y && \
    apt-get install python3-pip -y && \
    apt-get install awscli -y && \
    apt install python3-boto3 -y && \
    apt install python3-s3transfer && \
    apt-get install -y ant && \
    apt-get clean;

# Fix certificate issues
RUN apt-get update && \
    apt-get install ca-certificates-java && \
    apt-get clean && \
    update-ca-certificates -f;

# Setup JAVA_HOME -- useful for docker commandline
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/
RUN export JAVA_HOME

COPY ./requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

COPY ./Whelen_RTRadioAggregation.py .

CMD python3 ./Whelen_RTRadioAggregation.py