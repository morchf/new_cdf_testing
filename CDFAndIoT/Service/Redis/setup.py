#!/usr/bin/env python3

import os

from setuptools import find_namespace_packages, setup

namespace_package = "gtt.service.redis"
package_name = "redis-service"
source_dir = os.path.dirname(os.path.abspath(__file__))

# Read in readme.md for long_description
if os.path.exists(os.path.join(source_dir, "readme.md")):
    with open(os.path.join(source_dir, "readme.md"), encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = ""

requirements = [
    "wheel",
    "redis>=4.2",
    "boto3>=1.22",
    f"redis-data-model @ file://{os.path.join(source_dir, '../../DataModel/Redis')}",
]

setup(
    name=package_name,
    python_requires=">=3.8",
    description="Provides utility classes for subscribing and publishing to redis keys and channels",
    packages=find_namespace_packages(include=[namespace_package]),
    long_description=long_description,
    long_description_content_type="text/markdown",
    version="0.1",
    install_requires=requirements,
    url="https://github.com/gtt/smart-city-platform",
    license="Proprietary",
    classifiers=[
        "License :: Other/Proprietary License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
)
