#!/usr/bin/env python3

import os

from setuptools import find_packages, setup

package_name = "data-aggregation"
source_dir = os.path.dirname(os.path.abspath(__file__))

# Read in readme.md for long_description
if os.path.exists(os.path.join(source_dir, "readme.md")):
    with open(os.path.join(source_dir, "readme.md"), encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = ""

# load requirements from requirements.txt
with open(os.path.join(source_dir, "requirements.txt")) as f:
    requirements = f.read().splitlines()

setup(
    name=package_name,
    python_requires=">=3.8",
    description="Get batched raw data, transform to RT Radio Messages, save",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "aggregate_rt_radio_messages=data_aggregation.aggregate_rt_radio_messages:main",
        ],
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
    version="0.1",
    install_requires=requirements,
    author="Zachary Smithson",
    author_email="zach.smithson@gtt.com",
    url="https://https://github.com/gtt/smart-city-platform/tree/develop/Analytics/DataAggregation",
    license="Proprietary",
    classifiers=[
        "License :: Other/Proprietary License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
)
