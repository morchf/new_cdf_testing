#!/usr/bin/env python3

from pathlib import Path

from setuptools import find_namespace_packages, setup

namespace_package = "gtt.service.iot_core"
package_name = "iot-core-service"
source_dir = Path(__file__).parent.resolve()

# Read in readme.md for long_description
if (source_dir / "readme.md").exists():
    with open(str(source_dir / "readme.md"), encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = ""

requirements = [
    "wheel",
    "requests>=2.27.1",
    "boto3>=1.22.6",
    "redis>=4.2",
    f"asset-library-data-model @ file://{(source_dir / '../../DataModel/AssetLibrary').resolve()}",
    f"rt-radio-message-data-model @ file://{(source_dir / '../../DataModel/RTRadioMessage').resolve()}",
]

setup(
    name=package_name,
    python_requires=">=3.8",
    description="Easily serialize and deserialize RTRadioMessages, and load metadata from Asset Library",
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
