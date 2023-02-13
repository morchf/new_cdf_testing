"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import base64
from argparse import Namespace, ArgumentParser

import boto3
import requests


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        "--env", required=False, default="airflow-2-mwaa-dev-MwaaEnvironment"
    )
    parser.add_argument("--aws-profile", required=False, default="default")
    parser.add_argument("command", nargs="+")
    return parser.parse_args()


args = parse_args()
session = boto3.Session(profile_name=args.aws_profile)
client = session.client("mwaa")
print(args)

cli_token = client.create_cli_token(Name=args.env)
mwaa_response = requests.post(
    f'https://{cli_token["WebServerHostname"]}/aws_mwaa/cli',
    headers={
        "Authorization": f'Bearer {cli_token["CliToken"]}',
        "Content-Type": "text/plain",
    },
    data=(" ".join(args.command)),
)

response_json = mwaa_response.json()
err_message = base64.b64decode(response_json["stderr"]).decode("utf8")
out_message = base64.b64decode(response_json["stdout"]).decode("utf8")

print(mwaa_response.status_code)
print(err_message)
print(out_message)
