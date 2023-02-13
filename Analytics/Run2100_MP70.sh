#!/usr/bin/env bash
aws s3 cp s3://rt-radio-message/Scripts/Config_MP70.py .
aws s3 cp s3://rt-radio-message/Scripts/Config_2100.py .
aws s3 cp s3://rt-radio-message/Scripts/MP_70_RTRadioAggregation.py .
aws s3 cp s3://rt-radio-message/Scripts/RTRadioAggregation_2100.py .

sudo pip3 install boto3

#!/usr/bin/env python3
pyspark --jars /usr/lib/hadoop-lzo/lib/hadoop-lzo.jar
python3 MP_70_RTRadioAggregation.py
python3 RTRadioAggregation_2100.py
