#!/usr/bin/env python3

import logging

#logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=logging.INFO)
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(funcName)15s: %(message)s', level=logging.INFO)
logger = logging.getLogger()
log = logger

valid_device_templates = [
        'communicator',
        'vehiclev2',
        'phaseselector']

valid_group_templates = [
        'region',
        'agency']

