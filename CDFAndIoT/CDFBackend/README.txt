File description:
- aws-cert-auth.py
    - creates and deletes self-signed CAs certificates.
    - creates and deletes device certificates from these self-signed CAs.
- test-ca.py
    - is a unit test harness to execute all test cases related to aws-cert-auth.py
- mqtt-client.py
    - Used for testing. Sends messages to AWS Iot to verify certs are working.
- config.py
    - Config file for mqtt-client.py
    - MUST CHANGE ENDPOINT IN THIS FILE
- policy.templ
    - Example certificate policy file
- certs.py
    - certificate object: create, delete, etc
- thing.py
    - thing object: create, delete, etc
- misc.py
    - Support functions for policy, certs, thing

Prereqs:
1. Download AWS RootCA and name it RootCA.pem. Download from here:
    https://docs.aws.amazon.com/iot/latest/developerguide/server-authentication.html#server-authentication-certs
2. Modify the config.py with the appropriate AWS IoT Core endpoint
3. pip install boto3
4. pip install --upgrade —user awscli
5. AWS CLI credentials:
    > cd
    > mkdir .aws
    > cd .aws
    > <create config file with aws profile of choice>
    > <create credentials file with aws profile of choice>

Workflows:
1. Execute all test cases:
    > python test-ca.py
2. Use aws-cert-auth.py with appropriate arguments

Test cases:
- test_ca.py has three test cases. All tests delete all compo
    1. Tests the creation and deletion of the CA
    2. Test the creation and deletion of the CA and a device cert
    3. Test the creation of CA and device cert. Creates a thing. Create policy.
       Attaches policy to device cert. Attaches device cert to thing. Then
       send MQTT messages to the thing. AWS IoT test subscribe can be used
       to verify the receptions of these messages. Finals steps detach and remove
       everything: policy, cert, thing, CA.

General workflow notes:

Once created, CA and Device certificates are registered in AWS IoT Core, where they
can be viewed; CAs under AWS IoT->Secure->CAs, device certs under  AWS IoT->
Secure->Certificates.

Self-signed CA has an issuer and subject Common Name of the same value.
Device certiifcates created from a self-signed CA have an issuer CN equal
to that of the CA issuer CN, but the subject CN matches the device identifier.

The convention used in the examples is that CAs are: a1, a2, a3 ...
The convention used in the examples is that devices are: v1, v2, v3 ...
A thing name of a1_v1 identifies it as v1 device using a1 CA.

Use the MQTT simulator to connect and send data to the thing. Please note
the config.py file in this directory. Below are it's contents with
some explanation. Again, the thing name is 'a1_v1'.

# TLS connection cert related files
cafile_filename='RootCA.pem'
cert_filename='a1_v1.pem'
key_filename='a1_v1.key'

# AWS Iot end-point
client_id='a1_v1'
endpoint='xxxxxxxxxxxxxx-ats.iot.us-west-2.amazonaws.com'

IMPORTANT NOTE: the cafile_filename is the AWS RootCA.pem file. It is NOT
the self-signed CA file. This is required because the TLS client downloads
the cert from AWS upon the connection then uses RootCA.pem to verify the
chain of trust with the cert downloaded from AWS. The a1_v1.pem is uploaded
to AWS then the chain of trust is verified with the self-signed CA for a1.
