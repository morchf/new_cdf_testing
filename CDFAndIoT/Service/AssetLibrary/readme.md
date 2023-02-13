# AssetLibrary Service
This library is to aid development by facilitating interactions with AssetLibrary API. Instead of needing to deal with packaging data into json, sending requests, and parsing the response, this library will provide a wrapper around that to return the results as pydantic classes from the AssetLibrary DataModel.

While simplifying simple requests to a single line, this library is also responsible for abstracting away some of the AWS boilerplate like getting the endpoint URL, packaging requests using SigV4 authentication, etc.

Note that the corresponding AssetLibrary DataModel is a dependency, so there is no reason to add both libraries as client dependencies. Use the DataModel if you only need pydantic functionality, use the Service if you need both pydantic and higher-level functionality.

## ToDo
- expose the endpoint URL with a cloudformation output (or some central location) instead of requiring the `ASSET_LIBRARY_URL` environment variable to be set

## Installation
From root repo folder, else update the path to be this folder

``` bash
pip install -e CDFAndIoT/Service/AssetLibrary
```

For local develop, include the `-e` flag to allow an editable install

For production, include the `--use-feature=in-tree-build` flag to correctly handle relative imports if pip version is less than 21.3. Previously a temporary directory was created for builds which broke the relative path.

## Usage
```python

from gtt.service.asset_library import AssetLibraryAPI
asset_library_api = AssetLibraryAPI()

# queries device associated with the given vehicle id
vehicle_device_id = "union-city-vehicle-643"
vehicle = asset_library_api.get_device(device_id=vehicle_device_id)

print(vehicle)
```
