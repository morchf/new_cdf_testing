"""
    This file creates and deletes CA Certs and Device Certs.
    CA Certs get registered with AWS IOT Core.Device Certs
    get registered as device certs with AWS IOT Core.
    CA Certs can optional be configured JITR, which means that the first time
    a device that connects using a cert from CA with JITR gets registered.
    All the CA certs and Dev certs can listed.
    Any CA cert or Device Cert can be deleted.
"""
import boto3
import os

# import argparse
from zipfile import ZipFile, ZIP_DEFLATED

# import base64
# from botocore.exceptions import ClientError
import OpenSSL

subj_str = (
    "/C=US/ST=Minnesota/L=Oakdale/O=Global Traffic Technology/OU=Engineering/CN={}"
)
debug = False
days = 25 * 365  # All certs will expire in this many days
bucket = os.environ["CERT_BKT"]
tmp = "/tmp"  # Lambda is only allowed to write to the /tmp folder

# Create s3 client
s3 = boto3.client("s3")
iot = boto3.client("iot")

zip_pem_name = "cert.pem"
zip_key_name = "key.key"
zip_rootCA_name = "rootCA.pem"
zip_name = "filename.zip"

"""
    Create new root CA Cert
"""


def new_root_ca(region, jitr=True):

    rc = True
    try:
        # file names in tmp folder
        root_name = f"{region.upper()}_ROOTCA"
        cnf_name = f"{root_name}_openssl.conf"
        key_name = f"{root_name}.key"
        pem_name = f"{root_name}.pem"
        id_name = f"{root_name}_CERT_ID.txt"
        prefix = region.upper()
        # Create file structure for openssl
        create_openssl_dependencies()

        # Modify openssl conf for this root CA
        update_configuration_file(root_name)

        # Generate root CA private key
        generate_key(root_name)

        # Generate root CA cert
        try:
            ca_subj_str = subj_str.format(region)
            gen_ca_crt_cmd = (
                f"openssl req -x509 -new -key {tmp}/{key_name} -sha256 "
                f'-days {days} -out {tmp}/{pem_name} -subj "{ca_subj_str}"'
                f" -config {tmp}/{cnf_name} >> {tmp}/log.txt 2>> {tmp}/err.txt"
            )
            os.system(gen_ca_crt_cmd)
            if debug:
                print(f"gen_ca_crt_cmd = {gen_ca_crt_cmd}\n")
        except Exception as e:
            print(e)
            print("error: failed to generate root CA cert")

        # register CA with IoT Core
        ca_cert_id = register_ca_in_iot_core(root_name, days)

        # Activate the rootCA
        activate_ca(ca_cert_id, root_name, prefix)

        if jitr:
            # Enable Just-in-time-registration (JITR) on the CA
            enable_jitr(ca_cert_id, root_name, prefix)

        # Store key, pem, and cert id in S3
        store_cert_data(root_name, prefix)

        # Delete local copies
        try:
            os.remove(f"{tmp}/{cnf_name}")
        except Exception as e:
            print(e)
            print("error: failed to delete local copies")
        try:
            os.remove(f"{tmp}/{key_name}")
        except Exception as e:
            print(e)
            print("error: failed to delete local copies")
        try:
            os.remove(f"{tmp}/{pem_name}")
        except Exception as e:
            print(e)
            print("error: failed to delete local copies")
        try:
            os.remove(f"{tmp}/{id_name}")
        except Exception as e:
            print(e)
            print("error: failed to delete local copies")
        try:
            file_name = f"{tmp}/{root_name}.srl"
            os.remove(file_name)
        except Exception as e:
            print(e)
            print("error: failed to delete local copies")

        # Delete openssl file structure
        remove_openssl_dependencies()

    except Exception as e:
        print(f"new_root_ca(): Exception = {str(e)}\n")
        rc = False
    return rc


"""
    Create new subordinate CA Cert
"""


def new_sub_ca(region, agency, jitr=True):
    rc = True
    try:

        # files names
        root_name = f"{region.upper()}_ROOTCA"
        root_cnf_name = f"{root_name}_openssl.conf"
        root_key_name = f"{root_name}.key"
        root_pem_name = f"{root_name}.pem"

        sub_name = f"{region.upper()}_{agency.upper()}_SUBCA"
        sub_cnf_name = f"{sub_name}_openssl.conf"
        sub_key_name = f"{sub_name}.key"
        sub_pem_name = f"{sub_name}.pem"
        sub_csr_name = f"{sub_name}.csr"
        sub_id_name = f"{sub_name}_CERT_ID.txt"
        prefixRoot = region.upper()
        prefix = prefixRoot + "/AGENCIES/" + agency.upper()

        # Create file structure for openssl
        create_openssl_dependencies()

        # Get root CA key and pem; store in file
        get_cert_data(root_name, prefixRoot)

        # Modify root and sub CA openssl config for this sub CA
        update_configuration_file(root_name)
        update_configuration_file(sub_name)

        # Create cert
        generate_key(sub_name)

        # Request new CA
        try:
            ca_subj_str = subj_str.format(agency)
            gen_ca_crt_cmd = (
                f"openssl req -new -key {tmp}/{sub_key_name} -sha256"
                f' -days {days} -out {tmp}/{sub_csr_name} -subj "{ca_subj_str}"'
                f" -config {tmp}/{sub_cnf_name} >> {tmp}/log.txt 2>> {tmp}/err.txt"
            )
            os.system(gen_ca_crt_cmd)
            if debug:
                print(f"gen_ca_crt_cmd = {gen_ca_crt_cmd}\n")
        except Exception as e:
            print(e)
            print("error: failed to complete request for new CA")

        # Sign sub CA with root CA
        ca_sign_sub_cmd = (
            f"openssl ca -batch -config {tmp}/{root_cnf_name} -extensions"
            f" v3_intermediate_ca -days {days} -md sha256 -in "
            f"{tmp}/{sub_csr_name} -out {tmp}/{sub_pem_name} >> "
            f"{tmp}/log.txt 2>> {tmp}/err.txt"
        )
        os.system(ca_sign_sub_cmd)
        if debug:
            print(f"ca_sign_sub_cmd = {ca_sign_sub_cmd}\n")

        # Get CA registration code from AWS
        ca_cert_id = register_ca_in_iot_core(sub_name, days)

        # Activate the subCA
        activate_ca(ca_cert_id, sub_name, prefix)

        if jitr:
            # Enable Just-in-time-registration (JITR) on the CA
            enable_jitr(ca_cert_id, sub_name, prefix)

        # Store key, pem, and cert id in S3
        store_cert_data(sub_name, prefix)

        # Delete local copies
        try:
            os.remove(f"{tmp}/{root_cnf_name}")
        except Exception as e:
            print(e)
            print("error: failed to delete local copies1")
        try:
            os.remove(f"{tmp}/{root_key_name}")
        except Exception as e:
            print(e)
            print("error: failed to delete local copies2")
        try:
            os.remove(f"{tmp}/{root_pem_name}")
        except Exception as e:
            print(e)
            print("error: failed to delete local copies3")
        try:
            os.remove(f"{tmp}/{sub_cnf_name}")
        except Exception as e:
            print(e)
            print("error: failed to delete local copies4")
        try:
            os.remove(f"{tmp}/{sub_id_name}")
        except Exception as e:
            print(e)
            print("error: failed to delete local copies5")
        try:
            os.remove(f"{tmp}/{sub_key_name}")
        except Exception as e:
            print(e)
            print("error: failed to delete local copies6")
        try:
            os.remove(f"{tmp}/{sub_pem_name}")
        except Exception as e:
            print(e)
            print("error: failed to delete local copies7")
        try:
            os.remove(f"{tmp}/{sub_csr_name}")
        except Exception as e:
            print(e)
            print("error: failed to delete local copies8")
        try:
            file_name = f"{tmp}/{sub_name}.srl"
            os.remove(file_name)
        except Exception as e:
            print(e)
            print("error: failed to delete local copies9")

        # Delete openssl file structure
        remove_openssl_dependencies()

    except Exception as e:
        print(f"new_sub_ca(): Exception = {str(e)}\n")
        rc = False

    return rc


"""
    Create new Device Cert
"""


def new_dev(region, agency, device):

    rc = True
    try:
        # files names
        sub_name = f"{region.upper()}_{agency.upper()}_SUBCA"
        sub_key_name = f"{sub_name}.key"
        sub_pem_name = f"{sub_name}.pem"
        sub_srl_name = f"{sub_name}.srl"

        dev_name = f"{agency.upper()}_{device.upper()}"
        dev_key_name = f"{dev_name}.key"
        dev_pem_name = f"{dev_name}.pem"
        dev_csr_name = f"{dev_name}.csr"
        dev_id_name = f"{dev_name}_CERT_ID.txt"
        prefixSub = region.upper() + "/AGENCIES/" + agency.upper()
        prefix = prefixSub + "/DEVICES"

        # Create file structure for openssl
        create_openssl_dependencies()

        # Get sub CA key; store in file
        get_cert_data(sub_name, prefixSub)

        # Generate device key, csr, and cert
        dev_subj_str = subj_str.format(device)
        generate_key(dev_name)

        gen_dev_csr_cmd = (
            f"openssl req -new -key {tmp}/{dev_key_name}"
            f' -out {tmp}/{dev_csr_name} -subj "{dev_subj_str}">>'
            f" {tmp}/log.txt 2>> {tmp}/err.txt"
        )
        os.system(gen_dev_csr_cmd)
        if debug:
            print(f"gen_dev_csr_cmd = {gen_dev_csr_cmd}")

        gen_dev_crt_cmd = (
            f"openssl x509 -req -in {tmp}/{dev_csr_name}"
            f" -CA {tmp}/{sub_pem_name} -CAkey {tmp}/{sub_key_name}"
            f" -CAcreateserial -CAserial {tmp}/{sub_srl_name} -out "
            f"{tmp}/{dev_pem_name} -days {days} -sha256>> "
            f"{tmp}/log.txt 2>> {tmp}/err.txt "
        )
        os.system(gen_dev_crt_cmd)
        if debug:
            print(f"gen_dev_crt_cmd = {gen_dev_crt_cmd}")

        # Get device pem data
        with open(f"{tmp}/{dev_pem_name}", "r") as file:
            pem = file.read()
        file.close()

        # Get ca pem data
        with open(f"{tmp}/{sub_pem_name}", "r") as file:
            caPem = file.read()
        file.close()

        # validate device cert
        try:
            validate_cert_length(pem)
        except Exception as e:
            print(f"certificate failed validation with exception: {str(e)}")
            return

        # Register and activate the cert in AWS
        try:
            response = iot.register_certificate(
                certificatePem=pem, caCertificatePem=caPem, setAsActive=True
            )
        except Exception as e:
            print(f"Failed to register device cert in IoT Core error: {str(e)}")

        certId = response["certificateId"]

        # write cert ID to file
        with open(f"{tmp}/{dev_id_name}", "w") as file:
            file.write(certId)
        file.close()

        # Store pem, key, and cert id in S3
        store_cert_data(dev_name, prefix)

        # store zip of pem, key, and Amazon Root CA
        store_cert_data_as_zip(dev_name, prefix)

        # Delete local copies
        try:
            os.remove(f"{tmp}/{sub_key_name}")
        except Exception as e:
            print(e)
            print(f"error: failed to delete local copies of {sub_key_name}")
        try:
            os.remove(f"{tmp}/{sub_pem_name}")
        except Exception as e:
            print(e)
            print(f"error: failed to delete local copies of {sub_pem_name}")
        try:
            os.remove(f"{tmp}/{sub_srl_name}")
        except Exception as e:
            print(e)
            print(f"error: failed to delete local copies of {sub_srl_name}")
        try:
            os.remove(f"{tmp}/{dev_key_name}")
        except Exception as e:
            print(e)
            print(f"error: failed to delete local copies of {dev_key_name}")
        try:
            os.remove(f"{tmp}/{dev_pem_name}")
        except Exception as e:
            print(e)
            print(f"error: failed to delete local copies of {dev_pem_name}")
        try:
            os.remove(f"{tmp}/{dev_csr_name}")
        except Exception as e:
            print(e)
            print(f"error: failed to delete local copies of {dev_csr_name}")
        try:
            os.remove(f"{tmp}/{dev_id_name}")
        except Exception as e:
            print(e)
            print(f"error: failed to remove local copies of {dev_id_name}")

        # Delete openssl file structure
        remove_openssl_dependencies()

    except Exception as e:
        print(f"new_dev(): Exception = {str(e)}")
        rc = False
    return rc


"""
    Delete CDF entity resources based on what failed
"""


def entity_clean_up(name, prefix):
    cu = True
    try:
        entityType = name.split("_")[-1]
        ca_cert_id = get_cert_id(name.upper(), prefix)

        if ca_cert_id != "":
            if entityType == "ROOTCA":
                del_region_resources(ca_cert_id, name, prefix)
                print("Region Resources Deleted")
            elif entityType == "SUBCA":
                del_agency_resources(ca_cert_id, name, prefix)
                print("Agency Resources Deleted")
            else:
                del_dev_resources(ca_cert_id, name, prefix)
                print("Device Resources Deleted")
        else:
            cu = False
    except Exception as e:
        print(e)
        cu = False
    return cu


def del_region_resources(ca_cert_id, reg_name, prefix):
    deactivate_and_delete_ca(ca_cert_id)
    delete_cert_data(reg_name, prefix)


def del_agency_resources(ca_cert_id, agy_name, prefix):
    deactivate_and_delete_ca(ca_cert_id)
    delete_cert_data(agy_name, prefix)


def del_dev_resources(ca_cert_id, dev_name, prefix):
    deactivate_and_delete_cert(ca_cert_id)
    delete_cert_data(dev_name, prefix)
    delete_zip_data(dev_name, prefix)


"""
    Delete root CA Cert
"""


def del_root_ca(region):
    rc = True
    try:
        # file name
        root_name = f"{region.upper()}_ROOTCA"
        prefix = region.upper()

        # Get cert id
        ca_cert_id = get_cert_id(root_name, prefix)

        # Deativate and delete the rootCA on AWS
        deactivate_and_delete_ca(ca_cert_id)

        # Delete S3 data
        delete_cert_data(root_name, prefix)

    except Exception as e:
        print(f"del_root_ca(): Exception = {str(e)}")
        rc = False

    return rc


"""
    Delete sub CA Cert
"""


def del_sub_ca(region, agency):

    rc = True
    try:
        # file name
        sub_name = f"{region.upper()}_{agency.upper()}_SUBCA"

        # prefix - path to folder
        prefix = region.upper() + "/AGENCIES/" + agency.upper()

        # Get cert id from S3
        ca_cert_id = get_cert_id(sub_name, prefix)

        # Deativate and delete the subCA on AWS
        deactivate_and_delete_ca(ca_cert_id)

        # Delete S3 data
        delete_cert_data(sub_name, prefix)

    except Exception as e:
        print(f"del_sub_ca(): Exception = {str(e)}")
        rc = False

    return rc


"""
    Delete Device Cert
"""


def del_dev(region, agency, device):
    rc = True
    try:
        # file name
        dev_name = f"{agency.upper()}_{device.upper()}"

        # prefix - path to folder
        prefix = region.upper() + "/AGENCIES/" + agency.upper() + "/DEVICES"

        # Get cert id from S3
        cert_id = get_cert_id(dev_name, prefix)

        # Deativate and delete the device cert on AWS
        deactivate_and_delete_cert(cert_id)

        # Delete S3 data
        delete_cert_data(dev_name, prefix)

        # Delete zipped S3 data
        delete_zip_data(dev_name, prefix)

    except Exception as e:
        print(f"del_dev(): Exception = {str(e)}")
        rc = False
    return rc


"""
    Create directories and files in /tmp for openssl on Lambda
"""


def create_openssl_dependencies():

    try:
        new_dir = ["/tmp/certs", "/tmp/newcerts", "/tmp/crl", "/tmp/crlnumbers"]

        for dir in new_dir:
            os.mkdir(dir, 0o755)

        with open("/tmp/index.txt", "w") as file:
            file.write("")
        file.close()

        with open("/tmp/index.txt.attr", "w") as file:
            file.write("")
        file.close()

        with open("/tmp/serial", "w") as file:
            file.write("1000")
        file.close()
    except Exception as e:
        print(e)
        print("error: failed to create directories in /tmp for openssl on Lambda")


"""
    Remove directories and files in /tmp for openssl in Lambda
"""


def remove_openssl_dependencies():

    try:
        file_paths = [
            "/tmp/serial",
            "/tmp/index.txt",
            "/tmp/index.txt.attr",
            "/tmp/serial.old",
            "/tmp/index.txt.old",
            "/tmp/index.txt.attr.old",
            "/tmp/newcerts/1000.pem",
        ]

        for path in file_paths:
            if os.path.exists(path):
                os.remove(path)

    except OSError as e:
        print(f"Error: {path} : {e.strerror}")

    try:
        paths = ["/tmp/certs", "/tmp/newcerts", "/tmp/crl", "/tmp/crlnumbers"]

        for path in paths:
            if os.path.exists(path):
                os.rmdir(path)

    except OSError as e:
        print(f"Error: {path} : {e.strerror}")


"""
    List CA Certs
"""


def list_ca_certs():
    response = iot.list_ca_certificates()
    return response


"""
    List Device Certs
"""


def list_certs():
    response = iot.list_certificates()
    return response


"""
    List CA and Device Certs
"""


def list_all_certs():
    print("----- CA Certs -----")
    rc = list_ca_certs()
    print(rc)
    print("----- Device Certs -----")
    rc = list_certs()
    print(rc)


"""
    Create new key with openssl
"""


def generate_key(key_name):
    try:
        gen_dev_key_cmd = (
            f"openssl genrsa -out {tmp}/{key_name}.key 2048 "
            f">> {tmp}/log.txt 2>> {tmp}/err.txt"
        )
        rc = os.system(gen_dev_key_cmd)

        return rc
    except Exception as e:
        print(e)
        print("error: failed to create new key with openssl")


def validate_cert_length(cert):
    # Will throw an exception if cert not in correct PEM format
    OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, str(cert))


"""
    Generate new IoT Core registration code using AWS CLI
"""


def generate_iot_registration_code():
    try:
        response = iot.get_registration_code()
        reg_code = response["registrationCode"]
        if debug:
            print(f"reg_code = {reg_code}\n")

        return reg_code
    except Exception as e:
        print(e)
        print("error: failed to generate new IoT Core registration code using AWS CLI")


"""
    Generate verification cert and register CA with IoT Core
    Return caCertId
"""


def register_ca_in_iot_core(name, days):

    try:
        # Get CA registration code from AWS
        reg_code = generate_iot_registration_code()
        # Use reg code to generate verification key, csr, and cert
        generate_key("verificationCert")

        ver_crt_subj_str = subj_str.format(reg_code)
        gen_ver_csr_cmd = (
            f"openssl req -new -key {tmp}/verificationCert.key"
            f" -out {tmp}/verificationCert.csr -subj"
            f' "{ver_crt_subj_str}" >> {tmp}/log.txt 2>> {tmp}/err.txt'
        )
        os.system(gen_ver_csr_cmd)
        if debug:
            print(f"gen_ver_csr_cmd = {gen_ver_csr_cmd}\n")

        gen_ver_crt_cmd = (
            f"openssl x509 -req -in {tmp}/verificationCert.csr"
            f" -CA {tmp}/{name}.pem -CAkey {tmp}/{name}.key "
            f"-CAcreateserial -CAserial {tmp}/{name}.srl -out "
            f"{tmp}/verificationCert.pem -days {days} -sha256 "
            f">> {tmp}/log.txt 2>> {tmp}/err.txt"
        )
        os.system(gen_ver_crt_cmd)
        if debug:
            print(f"gen_ver_crt_cmd = {gen_ver_crt_cmd}\n")

        # Register root CA with the verification cert
        # Get pem data
        with open(f"{tmp}/{name}.pem", "r") as file:
            pem = file.read()
        file.close()

        # Get verification cert pem data
        with open(f"{tmp}/verificationCert.pem", "r") as file:
            ver = file.read()
        file.close()

        try:
            response = iot.register_ca_certificate(
                caCertificate=pem, verificationCertificate=ver
            )
        except Exception as e:
            print(f"Failed to register device cert in IoT Core error: {str(e)}")

        # Get cert_id
        caCertId = response["certificateId"]

        # Remove verification cert files
        try:
            os.remove(f"{tmp}/verificationCert.key")
        except Exception as e:
            print(e)
            print("error: failed to remove verification cert files")
        try:
            os.remove(f"{tmp}/verificationCert.csr")
        except Exception as e:
            print(e)
            print("error: failed to remove verification cert files")
        try:
            os.remove(f"{tmp}/verificationCert.pem")
        except Exception as e:
            print(e)
            print("error: failed to remove verification cert files")

        # write cert ID to file
        with open(f"{tmp}/{name}_CERT_ID.txt", "w") as file:
            file.write(caCertId)
        file.close()
        if debug:
            print(f"ca cert id = {caCertId}\n")

        return caCertId
    except Exception as e:
        print(e)
        print(
            "error: failed to generate verification cert and register CA with IoT core"
        )


"""
    Store pem, key and cert ID in S3
"""


def store_cert_data(name, prefix):
    pem_name = f"{name}.pem"
    key_name = f"{name}.key"
    id_name = f"{name}_CERT_ID.txt"

    # Get pem data
    try:
        with open(f"{tmp}/{pem_name}", "r") as file:
            pem = file.read()
        file.close()
    except Exception as e:
        print(e)
        print("error: failed to get pem data")

    # Get key data
    try:
        with open(f"{tmp}/{key_name}", "r") as file:
            priv_key = file.read()
        file.close()
    except Exception as e:
        print(e)
        print("error: failed to get key data")

    # Get cert_id
    try:
        with open(f"{tmp}/{id_name}", "r") as file:
            cert_id = file.read().replace("\n", "")
        file.close()
    except Exception as e:
        print(e)
        print("error: failed to get cert_id")

    # Store pem, key, and id in bucket for use later
    try:
        s3.put_object(Bucket=bucket, Key=f"{prefix}/{name}/{key_name}", Body=priv_key)
        s3.put_object(Bucket=bucket, Key=f"{prefix}/{name}/{pem_name}", Body=pem)
        s3.put_object(Bucket=bucket, Key=f"{prefix}/{name}/{id_name}", Body=cert_id)
    except Exception as e:
        print(f"put_object(): Exception = {str(e)}\n")
        entity_clean_up(name, prefix)


"""
    Store pem, key and cert ID in a zip in S3
"""


def store_cert_data_as_zip(name, prefix):
    pem_name = f"{name}.pem"
    key_name = f"{name}.key"
    zip_path = f"{tmp}/{zip_name}"

    try:
        zipObj = ZipFile(zip_path, "w", compression=ZIP_DEFLATED)
        zipObj.write(f"{tmp}/{pem_name}", arcname=zip_pem_name)
        zipObj.write(f"{tmp}/{key_name}", arcname=zip_key_name)
        zipObj.write("rootCA.pem")
        zipObj.close()

        # parse device SN from name, format is always agencyName_SN for devices
        # VPS stored at name
        sn = name.split("_")[-1]

        if sn in ["VPS", "2100"]:
            # Store zip in S3 to be served for VPS or 2100 later
            try:
                s3.upload_file(
                    Filename=zip_path,
                    Bucket=bucket,
                    Key=f"{prefix}/{name}/{zip_name}",
                    ExtraArgs={"ContentType": "application/zip"},
                )
            except Exception as e:
                print(f"put_object(): Exception = {str(e)}\n")
        else:
            # Store zip in S3 to be served for modem later
            try:
                s3.upload_file(
                    Filename=zip_path,
                    Bucket=bucket,
                    Key=f"{prefix}/{sn}/{zip_name}",
                    ExtraArgs={"ContentType": "application/zip"},
                )
            except Exception as e:
                print(f"put_object(): Exception = {str(e)}\n")

        # remove tmp files
        if os.path.exists(zip_path):
            os.remove(zip_path)
    except Exception as e:
        print(e)
        entity_clean_up(name, prefix)


"""
    Store pem and key from S3
"""


def get_cert_data(name, prefix):
    key_name = f"{name.upper()}.key"
    pem_name = f"{name.upper()}.pem"

    # Get key; store in file
    try:
        rc = s3.get_object(Bucket=bucket, Key=f"{prefix}/{name}/{key_name}")
        sub_key = rc["Body"].read().decode("utf-8")
    except Exception as e:
        print(f"get_object(): Exception = {str(e)}")

    with open(f"{tmp}/{key_name}", "w") as file:
        file.write(sub_key)
    file.close()

    # Get pem; store in file
    try:
        rc = s3.get_object(Bucket=bucket, Key=f"{prefix}/{name}/{pem_name}")
        sub_pem = rc["Body"].read().decode("utf-8")
    except Exception as e:
        print(f"get_object(): Exception = {str(e)}")

    with open(f"{tmp}/{pem_name}", "w") as file:
        file.write(sub_pem)
    file.close()


"""
    Delete pem, key and cert ID in S3
"""


def delete_cert_data(name, prefix):
    # Delete S3 data
    name = name.upper()
    try:
        rc = s3.delete_object(Bucket=bucket, Key=f"{prefix}/{name}/{name}.key")
        print(rc)
    except Exception as e:
        print(f"{name}.key file delete_object() failed: Exception = {str(e)}\n")
    try:
        rc = s3.delete_object(Bucket=bucket, Key=f"{prefix}/{name}/{name}.pem")
    except Exception as e:
        print(f"{name}.pem file delete_object() failed: Exception = {str(e)}\n")
    try:
        rc = s3.delete_object(Bucket=bucket, Key=f"{prefix}/{name}/{name}_CERT_ID.txt")
    except Exception as e:
        print(f"{name}_cert_id_txt file delete_object() failed: Exception = {str(e)}\n")


"""
    Delete zip in S3
"""


def delete_zip_data(name, prefix):
    # parse device SN from name, format is always agencyName_SN for devices
    # VPS/2100 stored at name
    sn = name.split("_")[-1]

    if sn in ["VPS", "2100"]:
        # Delete S3 data
        try:
            s3.delete_object(Bucket=bucket, Key=f"{prefix}/{name}/{zip_name}")
        except Exception as e:
            print(f"delete_object(): Exception = {str(e)}\n")
    else:
        try:
            s3.delete_object(Bucket=bucket, Key=f"{prefix}/{sn}/{zip_name}")
        except Exception as e:
            print(f"delete_object(): Exception = {str(e)}\n")


"""
    Update openssl configuration file for this CA
"""


def update_configuration_file(name):
    # parse which type of CA, rootCA or subCA
    ca = name.split("_")[-1]
    file_end = "_openssl.conf"

    # Create string for new conf file
    new_cnf = f"{name}{file_end}"

    # Create string for original conf file
    cnf_name = f"{ca}{file_end}"

    try:
        with open(f"{cnf_name}", "r") as file:
            conf_file = file.read()
        file.close()
    except Exception as e:
        print(e)
        print("error: failed to read file")

    # Replace generic CA data with data specific to this CA
    conf_file = conf_file.replace(ca, name)

    # Write to new configuration file
    with open(f"{tmp}/{new_cnf}", "w") as file:
        file.write(conf_file)
    file.close()


"""
    Get cert id from S3
"""


def get_cert_id(name, prefix):
    try:
        rc = s3.get_object(
            Bucket=bucket, Key=f"{prefix}/{name.upper()}/{name.upper()}_CERT_ID.txt"
        )
        if rc["ContentLength"] > 0:
            cert_id = rc["Body"].read().decode("utf-8")
        else:
            cert_id = ""

    except Exception as e:
        print(f"get_cert_id_from_cloud(): Exception = {str(e)}")
        # S3 call with throw an exception if no key found
        # set cert_id to known value
        cert_id = ""

    return cert_id


"""
    Deactivate and delete device certificate
"""


def deactivate_and_delete_cert(certId):
    try:
        iot.update_certificate(certificateId=certId, newStatus="INACTIVE")
        iot.delete_certificate(certificateId=certId)
    except Exception as e:
        print(e)
        print("error: failed to deactivate and delete device certificate")


"""
    Deactivate and delete CA certificate
"""


def deactivate_and_delete_ca(caCertId):
    try:
        iot.update_ca_certificate(certificateId=caCertId, newStatus="INACTIVE")
        iot.delete_ca_certificate(certificateId=caCertId)
    except Exception as e:
        print(e)
        print("error: failed to deactivate and delete CA certificate")


"""
    Activate CA certificate
"""


def activate_ca(caCertId, name, prefix):
    try:
        iot.update_ca_certificate(certificateId=caCertId, newStatus="ACTIVE")
    except Exception as e:
        print(e)
        print("error: failed to activate CA certificate")
        entity_clean_up(name, prefix)


"""
    Enable just in time registration on a CA
"""


def enable_jitr(caCertId, name, prefix):
    try:
        iot.update_ca_certificate(
            certificateId=caCertId, newAutoRegistrationStatus="ENABLE"
        )
    except Exception as e:
        print(e)
        print("error: failed to enable just in time registration on a CA")
        entity_clean_up(name, prefix)
