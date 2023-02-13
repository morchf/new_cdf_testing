# Redis Service

Provides neat abstractions for subscribing to and publishing to redis keys/channels.
Typically, we follow the pattern of publishing a kind of 'nothing' message on the
redis channel to notify subscribers that a change has been made and storing the
actual data in a plain cache that the subscriber will then look at. This abstraction
will combine those two steps for both the publisher and subscriber behind a neat little
interface.

## Installation

From root repo folder, else update the path to be this folder

```bash
pip install CDFAndIoT/Service/RTRadioMessage
```

For local develop, include the `-e` flag to allow an editable install

## Usage

The inline pydocs should be sufficient documentation for all use cases, however
further examples can be found on Confluence [here](https://gttwiki.atlassian.net/wiki/spaces/PD/pages/3191242844/Redis)
