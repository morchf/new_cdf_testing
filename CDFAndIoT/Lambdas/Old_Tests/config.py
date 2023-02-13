"""
  Config file for MQTT client. 
"""
import os

# Turn on/off logging
logging = True

# TLS connection cert related files
cafile_filename = "RootCA.pem"
cert_filename = "cert.pem"
key_filename = "private_key.pem"

# AWS Iot end-point
client_id = "GTTDevice"
endpoint = os.environ["IOT_CORE_ENDPOINT"]
