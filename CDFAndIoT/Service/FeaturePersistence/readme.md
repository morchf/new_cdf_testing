# FeaturePersistence Service
This library is to aid development by facilitating interactions with FeaturePersistence API. Instead of needing to deal with packaging data into json, sending requests, and parsing the response, this library will provide a wrapper around that to return the results as pydantic classes from the FeaturePersistence DataModel.

While simplifying simple requests to a single line, this library is also responsible for abstracting away some of the AWS boilerplate like getting the endpoint URL, packaging requests using SigV4 authentication, etc.

Note that the corresponding FeaturePersistence DataModel is a dependency, so there is no reason to add both libraries as client dependencies. Use the DataModel if you only need pydantic functionality, use the Service if you need both pydantic and higher-level functionality.

## ToDo
- expose the endpoint URL with a cloudformation output (or some central location) instead of requiring the `FEATURE_PERSISTENCE_URL` environment variable to be set
- add authentication support once added to the APIGateway configuration

## Installation
From root repo folder, else update the path to be this folder

``` bash
pip install -e CDFAndIoT/Service/FeaturePersistence
```

For local develop, include the `-e` flag to allow an editable install

For production, include the `--use-feature=in-tree-build` flag to correctly handle relative imports if pip version is less than 21.3. Previously a temporary directory was created for builds which broke the relative path.

## Usage
ToDo
