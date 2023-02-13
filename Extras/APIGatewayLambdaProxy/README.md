# Using OpenAPI specifications with API Gateway and Lambda
An example of using an OpenAPI 3.0 specification to generate a REST API in API Gateway with Lambda integrated as the back-end.

## Introduction
Inside this folder, you'll find source code for three Lambda functions (in the `create`, `get`, `delete` folders) and a SAM template `template.yaml` that deploys the entire example application.

You need to have the SAM CLI installed to deploy the application. Follow the instructions [here](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) for your platform to install it.

When you have SAM configured properly, deploy the application using `sam deploy --guided`.

## Application
The application is defined in `template.yaml`. It is composed of:

- An OpenAPI 3.0 specification inlined into the template as the `Resources.Api.Properties.DefinitionBody` property. The spec defines three API methods: `POST /pet`, `GET /pet/{petId}`, and `DELETE /pet/{petId}`.
- A Lambda function to handle each API method.

The API spec is used to create resources, methods, and models in API Gateway, and is extended with API Gateway-specific properties identified by `x-amazon-apigateway-*` to define the Lambda integrations.

## API Gateway integration
The role of API Gateway in this example application is to:
- Validate the request body of the `POST /pet` method based on the request body definition provided in the API spec. Return a `400` response if the request body fails schema validation.
- For all requests, pass the client request through to the corresponding Lambda function without transformation. The return value of the function is passed through as the response without transformation. This accomplished using the "Lambda proxy integration" configuration setting (an `x-amazon-apigateway-integration.type` of `aws_proxy` in the application template).

When inspecting the API in the API Gateway console, observe that the "Method Request" and "Method Response" for each method automatically adopt the definition of request bodies (if applicable), possible response codes, and response bodies (if applicable) from the API spec.
