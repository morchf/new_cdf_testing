# Retrieve Opticom Logs

## Description
This is a small tool that can be used for QA and testing purposes.  It allows the user to run a lambda function that then pulls the opticom logs from a customer EC2 database for a SCP solution.  The data is then written to a file in S3 that is queryable in AWS Athena.  Sample queries for analyzing the logs are stored in the "Queries" folder.

## Usage
Required fields in the Lambda Test Event:
- customerName          Agency Name from which the logs will be retrieved
- locationNames         Intersection for which logs will be retrieved
- timeFrom              Filter to choose the start time of which logs will be retrieved
- timeTo                Filter to choose the end time of which logs are retrieved

Sample Test Event for the Lambda:
{
    "customerName": "HOKAH",
    "locationNames": "intersection1,TestIntersection1,TestIntersection17",
    "timeFrom": "2020-09-17 11:00:00",
    "timeTo": "2021-03-21 11:19:00"
}