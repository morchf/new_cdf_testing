# GTT / Constructs / CDK

Common resources for CDK deployment. [CDK Docs](https://docs.aws.amazon.com/cdk/api/v2)

## Getting Started

## Creating a New App

Create a CDK stack with a top-level project

```python
from gtt.constructs.cdk import App

from .modules import NamedModule


class CoreApp(Stack):
    def __init__(self, scope: Construct, **kwargs) -> None:
        super().__init__(scope, **kwargs)

        # Existing
        self.__template = cfn_inc.CfnInclude(
            self, "Template", template_file="CloudFormationFile.yml"
        )
        self.__api = self.__template.get_resource("ResourceName")

        # Module existing under app
        NamedModule(
            self,
            id="Name",
            rest_api_ref=self.__api.ref,
            rest_api_root_resource_id=self.__api.attr_root_resource_id
        )


"""
AWS_PROFILE=develop cdk synth --show-template > OutputStack.yml

'project_id' corresponds to top-level folder
'app_id' corresponds to specific sub-deployment

Bootstrap a CloudFormation stack with stack name 'ClientAPI-Analytics'
"""
with App(
    project_id="ClientAPI",
    app_id="Analytics",
    environment="develop",
    owner="jacob.sampson",
) as app:
    CoreApp(**app.kwargs)
```
