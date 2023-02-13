# Import-Whelen-Assets-API

Here we create an API endpoint to execute task on demand.

The "agency_guid" will be provided in the API Request and the task will first get all assets from Whelen API for that agency, compare all missing assets with CDF, and use the "Asset Lib endpoints" API to create these assets in CDF.

## Usage
Create and publish an API endpoint with the method "POST" using API Gateway and connect it to a lambda function that will trigger a batch processing using Long Running Queue Job.

Lambda function will be a python script that will take in an agency guid and send it to a secondary Lambda for processing.

## Workflow of the script:
1. Get "agency_guid" from message attributes received by SQS.
2. Get Whelen Vehicles and agency info for this "agency_guid".
3. Get CDF devices list for this "agency_guid".
4. Get missing whelen vehicles list -> get_delta.
5. Flag dyanmo stating that the state is "syncing" now we have assets to import.
6. Import those vehicles in CDF.
7. Flag the agency in dynamo as "sync_completed" -> in import_delta.
8. Delete the message from the SQS Queue.

## States of the feature in DynamoDb:
- These features would reflect the state of that agency's feature.
- The UI will read these features and reflect the corresponding messages on the UI to the user.
1. "unsynced": The agency is not in-sync with CDF and Feature's Cloud.
2. "syncing": The lambda is processing the import of vehicles in CDF.
3. "synced": The vehicles are imported successfully and the agency is in-sync with CDF.
4. "failed_to_sync": There is some error in the processing of lambda.

## Why lambda and not AWS Batch?
- Initial testing of the functionality was done on AWS Batch, where the Lambda fires a Batch Job on demand, and this job will execute a container with the above script.
- Although, the response time to spin up an Ec2 instance and executing the task each time is almost 1-2.5 minutes, the latency is too much, since this is a time sensitive task.
- We could keep the Ec2 running all the time, in which case the response time is around 5-10 seconds, which is good, but the cost of keeping the ec2 running will build up.

### Conclusion: Lambda proves best in this use case.
- With an average response time to import 100 assets from Whelen to CDF: 30 - 35 seconds.
- Average response time to import 1 asset from Whelen to CDF: 2 seconds. 

### Observation: API Gateway times out after 29 seconds.
#### soln: Add SQS between API Gateway and Lambda.
- With the use case of importing 100 assets with lambda directly, the API Gateway times out after 29 seconds(default setting), but we do not want that. 
- In this case, we connect the API Gateway to SQS queue, and the SQS Queue will trigger the lambda and dump the API request to the queue.
- Pass in the queryStringParameters using "MessageAttributes". Check this (link)[https://github.com/serverless-operations/serverless-apigateway-service-proxy/issues/45] here.