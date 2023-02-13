#!/usr/bin/env python3

from pathlib import Path

from setuptools import find_namespace_packages, setup

namespace_package = "gtt.constructs.cdk"
source_dir = Path(__file__).parent.absolute()

try:
    long_description = Path(source_dir / "README.md", encoding="utf-8").read_text()
except Exception:
    long_description = ""

requirements = Path(source_dir / "requirements.txt").read_text()

setup(
    name=namespace_package.replace(".", "_"),
    python_requires=">=3.8",
    description="Basic constructs for spinning up resources using CDK",
    packages=find_namespace_packages(include=[namespace_package]),
    long_description=long_description,
    long_description_content_type="text/markdown",
    version="0.1",
    install_requires=requirements,
    author="Jacob Sampson",
    author_email="jacob.sampson@gtt.com",
    url="https://github.com/gtt/smart-city-platform",
    license="Proprietary",
    classifiers=[
        "License :: Other/Proprietary License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
)
