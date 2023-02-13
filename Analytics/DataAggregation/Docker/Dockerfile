# Dockerfile, Image, container

# base image
FROM bitnami/spark

USER root

COPY ./Docker/requirements.txt ./Analytics/requirements.txt
RUN pip install --no-cache-dir -r ./Analytics/requirements.txt

# Add Aggregation scripts to container
COPY setup.py ./Analytics
COPY data_aggregation ./Analytics/data_aggregation
RUN pip install --no-cache-dir ./Analytics

# Copy shell script to download and run all these aggregation scripts.
COPY ./Docker/start-aggregation-jobs.sh ./Analytics

# Remove the \r from the filename if running on Windows Docker - Or use 'LF' as your
# end of line sequence
# RUN sed "s/\r$//" start-aggregation-jobs.sh

# Give executable permissions to shell script
RUN chmod +x ./Analytics/start-aggregation-jobs.sh

CMD ./Analytics/start-aggregation-jobs.sh