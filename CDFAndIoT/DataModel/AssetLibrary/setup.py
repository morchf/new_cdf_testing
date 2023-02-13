#!/usr/bin/env python3

import os

from setuptools import find_namespace_packages, setup

namespace_package = "gtt.data_model"
package_name = "asset-library-data-model"
source_dir = os.path.dirname(os.path.abspath(__file__))

# Read in readme.md for long_description
if os.path.exists(os.path.join(source_dir, "readme.md")):
    with open(os.path.join(source_dir, "readme.md"), encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = ""

requirements = [
    "wheel",
    "pydantic>=1.9.1",
]

setup(
    name=package_name,
    python_requires=">=3.8",
    description="Data Model with pydantic classes for AssetLibrary API",
    packages=find_namespace_packages(include=[namespace_package]),
    long_description=long_description,
    long_description_content_type="text/markdown",
    version="0.1",
    install_requires=requirements,
    author="Zachary Smithson",
    author_email="zach.smithson@gtt.com",
    url="https://github.com/gtt/smart-city-platform",
    license="Proprietary",
    classifiers=[
        "License :: Other/Proprietary License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
)
