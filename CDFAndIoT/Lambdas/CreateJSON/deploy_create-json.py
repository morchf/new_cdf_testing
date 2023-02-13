#!/usr/bin/env python

import os
import shutil


def deploy():
    # Change bucket to account specific lambda zips bucket
    bkt = "gtt-lambda-zips-us-west-2"
    name = "create-json"

    home = os.getcwd()
    # put required libraries in package directory
    cmd = f"pip install -r requirements.txt --target={home}/lambda-code"
    os.system(cmd)
    print(cmd)

    # os.chdir('package')
    # print('cd package')

    # copy files from aws-cert-auth to package directory
    to_copy = [
        "agency.py",
        "asset_lib.py",
        "aws_cert_auth.py",
        "certs.py",
        "config_asset_lib.py",
        "device.py",
        "iot_core.py",
        "misc.py",
        "policy.py",
        "region.py",
        "status.py",
        "thing.py",
        "ui.py",
        "location.py",
        "rootCA_openssl.conf",
        "subCA_openssl.conf",
        "Policy.templ",
        "rootCA.pem",
    ]

    for thing in to_copy:
        old_dir = os.path.join("../../extras/aws-cert-auth", thing)
        shutil.copy(old_dir, os.getcwd() + "/lambda-code")

    # add lambda to zip
    cmd = f"zip -r9 {name}.zip {home}/lambda-code/."
    os.system(cmd)
    print(cmd)

    # upload to s3
    cmd = f"aws s3 cp {name}.zip s3://{bkt}"
    os.system(cmd)
    print(cmd)

    # remove zip file
    cmd = f"rm {name}.zip"
    os.system(cmd)
    print(cmd)


def main():
    deploy()


if __name__ == "__main__":
    main()
