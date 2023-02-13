#!/usr/bin/env python

import os
import shutil


def deploy():
    # Change bucket to account specific lambda zips bucket
    bkt = "gtt-lambda-zips-us-west-1-act"

    home = os.getcwd()
    # put required libraries in package directory
    cmd = "pip install --target ./package requests"
    os.system(cmd)
    print(cmd)

    os.chdir("package")
    print("cd package")

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
        "rootCA_openssl.conf",
        "subCA_openssl.conf",
        "Policy.templ",
        "rootCA.pem",
        "location.py",
    ]

    for thing in to_copy:
        old_dir = os.path.join("../CDFBackend", thing)
        shutil.copy(old_dir, os.getcwd())

    # zip package directory
    cmd = f"zip -r9 {home}/delete-cdf.zip ."
    os.system(cmd)
    print(cmd)

    os.chdir(home)
    print("cd ..")

    # add lambda to zip
    cmd = "zip -g delete-cdf.zip ./lambda-code/delete-cdf.py"
    os.system(cmd)
    print(cmd)

    # upload to s3
    cmd = f"aws s3 cp delete-cdf.zip s3://{bkt}"
    os.system(cmd)
    print(cmd)

    # remove package directory
    cmd = "rm -rf package"
    os.system(cmd)
    print(cmd)

    # remove zip file
    cmd = "rm delete-cdf.zip"
    os.system(cmd)
    print(cmd)


def main():
    deploy()


if __name__ == "__main__":
    main()
