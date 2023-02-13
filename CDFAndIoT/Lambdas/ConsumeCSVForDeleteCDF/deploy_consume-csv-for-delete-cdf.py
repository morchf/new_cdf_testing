#!/usr/bin/env python

import os
import shutil

def deploy():
    # Change bucket to account specific lambda zips bucket
    bkt = 'gtt-lambda-zips-us-west-1-act'

    home = os.getcwd()

    # add lambda to zip
    cmd = 'zip -r9 consume-csv-for-delete-cdf.zip ./lambda-code/consume-csv-for-delete-cdf.py'
    os.system(cmd)
    print(cmd)

    # upload to s3
    cmd = f'aws s3 cp consume-csv-for-delete-cdf.zip s3://{bkt}'
    os.system(cmd)
    print(cmd)

    # remove package directory
    cmd = 'rm -rf package'
    os.system(cmd)
    print(cmd)

    # remove zip file
    cmd = 'rm consume-csv-for-delete-cdf.zip'
    os.system(cmd)
    print(cmd)


def main():
    deploy()

if __name__ == "__main__":
    main()