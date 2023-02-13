# set the base image to ubuntu
FROM ubuntu

ENV DEBIAN_FRONTEND=noninteractive

ENV TZ=America/Chicago
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# replace shell with bash so we can source files
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

# create base system
RUN apt-get -y update \
    && apt-get -y upgrade \
    && apt-get -y autoclean 


RUN apt-get install -y \
    curl \ 
    zip \
    git \
    vim \
    python3-pip \
    jq

# install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install

# nvm environment variables
ENV NVM_DIR /root/.nvm
ENV NODE_VERSION 12

# install nvm
# https://github.com/creationix/nvm#install-script
RUN curl --silent -o- https://raw.githubusercontent.com/creationix/nvm/v0.31.2/install.sh | bash

# install node, npm, pnpm
RUN source $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && nvm use default \
    && npm install -g pnpm@3.5.3

# add node and npm to path so the commands are available
ENV NODE_PATH $NVM_DIR/v$NODE_VERSION/lib/node_modules
ENV PATH $NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH

RUN mkdir /root/.aws
COPY ./config /root/.aws/config
COPY ./credentials /root/.aws/credentials
COPY ./requirements.txt /root/requirements.txt

RUN cd
RUN pip3 install -r /root/requirements.txt
RUN export=AWS_PROFILE=default
RUN alias py=python3
