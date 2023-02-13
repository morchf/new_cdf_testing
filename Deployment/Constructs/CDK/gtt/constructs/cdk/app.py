from os import getenv
from typing import Literal, Optional, Union

from aws_cdk import App as CdkApp
from aws_cdk import Environment

EnvironmentStr = Union[
    Literal["develop"],
    Literal["test"],
    Literal["production"],
    Literal["pilot"],
]


class App:
    """
    Base CDK stack app

    See: https://docs.aws.amazon.com/cdk/api/v2/
    """

    @property
    def scope(self):
        return self.__app

    @property
    def id(self):
        return self.__id

    @property
    def env(self) -> Environment:
        """CDK environment"""
        return self.__env

    @property
    def environment(self) -> EnvironmentStr:
        """String environment

        Returns:
            EnvironmentStr: String enum for environment
        """
        return self.__environment

    @property
    def kwargs(self):
        return {
            "id": self.id,
            "env": self.env,
            "scope": self.scope,
            "environment": self.environment,
            **({} if self.__tags is None else {"tags": self.__tags}),
        }

    def __init__(
        self,
        project_id: str,
        app_id: str,
        *,
        account: Optional[str] = None,
        region: Optional[str] = None,
        owner: Optional[str] = None,
        environment: Optional[EnvironmentStr] = None,
    ):
        assert project_id
        assert app_id

        self.__account = account or getenv(
            "CDK_DEPLOY_ACCOUNT", getenv("CDK_DEFAULT_ACCOUNT")
        )
        self.__region = region or getenv(
            "CDK_DEPLOY_REGION", getenv("CDK_DEFAULT_REGION")
        )

        self.__environment: EnvironmentStr = environment or getenv(
            "ENVIRONMENT", getenv("Env", "develop")
        )

        assert self.__account
        assert self.__region

        self.__app = CdkApp()
        self.__id = f"{project_id}-{app_id}"
        self.__env = Environment(
            account=getenv("CDK_DEPLOY_ACCOUNT", getenv("CDK_DEFAULT_ACCOUNT")),
            region=getenv("CDK_DEPLOY_REGION", getenv("CDK_DEFAULT_REGION")),
        )

        self.__tags = {"Project": project_id, "App": app_id}

        if environment is not None:
            self.__tags["Environment"] = environment

        if owner is not None:
            self.__tags["Owner"] = owner

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.scope.synth()
