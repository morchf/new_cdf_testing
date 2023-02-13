#!/usr/bin/env python3

import os

from setuptools import find_packages, setup

package_name = "tsp-gtfs-realtime"
source_dir = os.path.dirname(os.path.abspath(__file__))

# Read in readme.md for long_description
if os.path.exists(os.path.join(source_dir, "readme.md")):
    with open(os.path.join(source_dir, "readme.md"), encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = ""

requirements = [
    "wheel",
    "protobuf==3.20.1",
    "gtfs-realtime-bindings==0.0.7",
    "requests==2.27.1",
    "boto3==1.22.6",
    "redis==4.2.2",
    "pause==0.3",
    "docker==5.0.3",
    "pandas==1.4.2",
    "pyarrow==7.0.0",
    "pydantic==1.9.1",
    "requests_aws_sign==0.1.6",
    f"feature-persistence-service @ file://{os.path.join(source_dir, '../../CDFAndIoT/Service/FeaturePersistence')}",
    f"iot-core-service @ file://{os.path.join(source_dir, '../../CDFAndIoT/Service/IoTCore')}",
]

# Requirements could be split for minimal installs for services (docker, protobuf, etc)
dev_requirements = ["black", "flake8", "nbconvert"]
test_requirements = []
jupyter_requirements = ["jupyter", "ipykernel", "pandas", "tabulate", "beautifulsoup4"]
all_requirements = dev_requirements + test_requirements + jupyter_requirements

setup(
    name=package_name,
    python_requires=">=3.8",
    description="Subscribe to gtfs feed, notify subscribers, and keep redis database updated",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "gtfs-realtime-api-poller=tsp_gtfs_realtime.gtfs_realtime_api_poller:main",
            "agency-manager=tsp_gtfs_realtime.agency_manager:main",
            "vehicle-manager=tsp_gtfs_realtime.vehicle_manager:main",
            "data-aggregator=tsp_gtfs_realtime.data_aggregator:main",
        ],
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
    version="0.1",
    install_requires=requirements,
    extras_require={
        "all": all_requirements,
        "dev": dev_requirements,
        "test": test_requirements,
        "jupyter": jupyter_requirements,
    },
    author="Zachary Smithson",
    author_email="zach.smithson@gtt.com",
    url="https://github.com/gtt/tsp-gtfs-realtime",
    license="Proprietary",
    classifiers=[
        "License :: Other/Proprietary License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
)
