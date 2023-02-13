# Implementing Sessions with Cognito and Node.js
Presented here is an example implementation of delegating authentication to
AWS Cognito in the context of a Node.js Express-based web application.

This example implements the design laid out on the page [_Cognito for SCP User Authentication_](https://gttwiki.atlassian.net/wiki/spaces/PD/pages/1313308679/Cognito+for+SCP+User+Authentication?atlOrigin=eyJpIjoiN2U1NTdjNGQ5MmY4NGIyYWI4YTMxZDhhOWU0MjlmMTMiLCJwIjoiYyJ9).

## Components
There are two main components:

- An Express server (`app.js`) that has routes that serve pages (Handlebars templates in `views/`) and routes that serve as an API (`routes/api.js`).
- A CloudFormation template (`cognito-session.yaml`) to deploy and configure a simple Cognito user pool, OAuth app client, and hosted authentication service for use with the server application.

## Getting started

### Deploy Cognito
Deploy the `cognito-session.yaml` template to the region of your choice using the CloudFormation console.

This will create a user pool with a random name like `UserPool-1234abcde`.

### Create a user
The Cognito user pool is configured to only allow administrators to create users, so you must create a user in the Cognito console.

When your test user signs in for the first time, they will be asked to create a new password. This happens in the Cognito-hosted authentication UI, outside of the server application.

### Configure the server application
From inside this directory, run `npm install` to install dependencies. Then create a file named `.env` in this directory that contains the following:
```
COGNITO_USER_POOL_ID=
EXPRESS_PORT=3000
EXPRESS_SESSION_SECRET=shhhhh
OAUTH_AUTHZ_URL=
OAUTH_TOKEN_URL=
OAUTH_CLIENT_ID=
OAUTH_CLIENT_SECRET=
```
Fill in the blank values using the Cognito console.

The `OAUTH_AUTHZ_URL` will be of the form `https://<domain>.auth.<region>.amazoncognito.com/authorize` and the `OAUTH_TOKEN_URL` will be of the form `https://<domain>.auth.<region>.amazoncognito.com/token`, where `<domain>` is the domain prefix you chose when deploying the Cognito stack, and `<region>` is the region the stack was deployed to.

Cognito is configured to redirect authentication requests to `http://localhost:3000/login`, so if you change `EXPRESS_PORT`, you will need to change the app client settings in the Cognito console to match.

### AWS SDK
The server application uses the AWS SDK. You will need to have the AWS CLI configured with default credentials and a region that is the same as where you deployed Cognito.

Before starting the server application, set the environment variable `AWS_SDK_LOAD_CONFIG=true`.

### Start the server
Start the server by running `npm start`. You can interact with the application in a web browser by navigating to `http://localhost:3000`.

## Note
The use of delegated authentication introduces two levels of "signing in." The first is the user "signing in" to Cogntio, which happens on the Cognito-hosted authentication page. The second is the user "signing in" to the _application_, which happens automatically (and invisibly) immediately after signing in to Cognito.

**This means that even when the user signs _out_ of the application, they are still signed in to Cognito until Cognito's session expires.**

Clicking the sign-in link from the application will not require the user to re-authenticate with Cognito, because they are already authenticated.
