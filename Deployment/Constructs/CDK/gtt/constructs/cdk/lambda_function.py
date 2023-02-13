import subprocess
from pathlib import Path, PosixPath
from typing import List, Optional, Union

from aws_cdk import Duration, RemovalPolicy, aws_lambda
from constructs import Construct


class LocalLambdaLayer(Construct):
    @property
    def layer(self) -> aws_lambda.LayerVersion:
        return self.__layer

    def __init__(
        self,
        scope: Construct,
        id: str,
        layer_name: str,
        requirements_file: str,
        runtime: aws_lambda.Runtime = aws_lambda.Runtime.PYTHON_3_8,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        self.__layer = self._create_layer(
            layer_name=layer_name, requirements_file=requirements_file, runtime=runtime
        )

    def _create_layer(
        self,
        layer_name: str,
        requirements_file: str,
        runtime: aws_lambda.Runtime,
        *,
        compatible_runtimes: Optional[List[aws_lambda.Runtime]] = None,
        **kwargs,
    ) -> aws_lambda.LayerVersion:
        """
        Dynamically build a Lambda layer

        Assumes relative requirements are relative to the requirements file
        location

        Stores zipped layer in '/tmp/layers/<layer_name>'
        """
        if compatible_runtimes is None:
            compatible_runtimes = [runtime]

        subprocess.run(
            [
                "pip",
                "install",
                "-t",
                f"/tmp/layers/{layer_name}/python/lib/{runtime.to_string()}/site-packages",
                "-r",
                str(Path(requirements_file).name),
                "--upgrade",
            ],
            cwd=str(Path(requirements_file).parent.absolute()),
        )

        return aws_lambda.LayerVersion(
            scope=self,
            id=layer_name,
            code=aws_lambda.Code.from_asset(f"/tmp/layers/{layer_name}"),
            compatible_runtimes=compatible_runtimes,
            removal_policy=RemovalPolicy.DESTROY,
            **kwargs,
        )


class LocalLambda(Construct):
    @property
    def function(self) -> aws_lambda.Function:
        return self.__function

    def __init__(
        self,
        scope: Construct,
        id: str,
        function_name: str,
        code_dir: str,
        base_dir: Optional[str] = None,
        layers: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(scope, id)

        self.__function_name = function_name
        self.__code_dir = f"{base_dir}/{code_dir}" if base_dir is not None else code_dir

        self.__layers = layers if layers is not None and len(layers) > 0 else None

        self.__function = self._create_lambda(
            f"{id}Lambda",
            function_name=self.__function_name,
            code_dir=self.__code_dir,
            layers=self.__layers,
            **kwargs,
        )

    def _create_lambda(
        self,
        id: str,
        function_name: str,
        code_dir: Union[str, PosixPath],
        handler: str = "app.handler",
        runtime: int = aws_lambda.Runtime.PYTHON_3_8,
        timeout: int = Duration.seconds(30),
        memory_size: int = 128,
        **kwargs,
    ) -> aws_lambda.Function:
        return aws_lambda.Function(
            self,
            id,
            function_name=function_name,
            code=aws_lambda.Code.from_asset(
                str(code_dir), exclude=["requirements.txt", "__tests__"]
            ),
            handler=handler,
            runtime=runtime,
            timeout=timeout,
            memory_size=memory_size,
            **kwargs,
        )
