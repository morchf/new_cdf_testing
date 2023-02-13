#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of gtt.service.phase_selector
# https://github.com/gtt/smart-city-platform

# Licensed under the  license:
# http://www.opensource.org/licenses/-license
# Copyright (c) 2022, Jacob Sampson <jacob.sampson@gtt.com>

from pathlib import Path

from setuptools import find_namespace_packages, setup

namespace_package = "gtt.service.phase_selector"
package_name = "gtt_service_phase_selector"
source_dir = Path(__file__).parent.absolute()

try:
    long_description = Path(source_dir / "README.md", encoding="utf-8").read_text()
except Exception:
    long_description = ""

requirements = Path(source_dir / "requirements.txt").read_text()

setup(
    name=package_name,
    version="0.1.0",
    python_requires=">=3.8",
    description="Phase selector interactions",
    packages=find_namespace_packages(include=[namespace_package]),
    long_description=long_description,
    long_description_content_type="text/markdown",
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
