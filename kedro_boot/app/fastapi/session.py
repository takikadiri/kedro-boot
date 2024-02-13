import inspect
import logging
import threading
import typing
import uuid


try:  # For backward compatibility with python 3.8
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

from fastapi import Depends, FastAPI, Request

from kedro_boot.framework.compiler.specs import CompilationSpec
from kedro_boot.framework.session import KedroBootSession

LOGGER = logging.getLogger(__name__)


class KedroFastApiSession:
    def __init__(self, session: KedroBootSession = None) -> None:
        self.session = session

    async def __call__(self, request: Request):
        itertime_params = request.path_params
        parameters = request.query_params._dict
        namespace = request.scope["route"].operation_id
        datasets = {}

        # TODO: We should get pipeline inputs and outputs from KedroFastApi session instead of KedroBootSession. We should persist it after compilation.

        pipeline_inputs = (
            self.session._context._namespaces_registry.get(namespace).get("spec").inputs
        )

        if pipeline_inputs:
            datasets = await request.json()
            if len(pipeline_inputs) == 1:
                datasets = {pipeline_inputs[0]: datasets}

        run_id = uuid.uuid4().hex
        itertime_params.update({"run_id": run_id})

        pipeline_outputs = (
            self.session._context._namespaces_registry.get(namespace)
            .get("spec")
            .namespaced_outputs
        )
        if (
            inspect.iscoroutinefunction(request.scope["endpoint"])
            and not pipeline_outputs
        ):
            LOGGER.info(f"Running {request.scope['endpoint'].__name__} in background")
            background_thread = threading.Thread(
                target=self.session.run,
                args=(namespace, datasets, parameters, itertime_params, run_id),
            )
            background_thread.start()
            return {
                "message": f"Running {request.scope['endpoint'].__name__} in background. You can refer to the resource details to identify the logs and get the run state",
                "resource": {
                    "run_id": run_id,
                    "namespace": namespace or "None",
                    "parameters": parameters,
                    "itertime_params": itertime_params,
                },
            }

        return self.session.run(
            namespace=namespace,
            inputs=datasets,
            parameters=parameters,
            itertime_params=itertime_params,
            run_id=run_id,
        )

    def compile(self, app: FastAPI) -> None:
        compilation_specs = []

        for route in app.routes:
            if hasattr(route, "endpoint") and hasattr(
                route.endpoint, "__annotations__"
            ):
                managed_endpoints = {
                    endpoint_name: endpoint_type
                    for endpoint_name, endpoint_type in route.endpoint.__annotations__.items()
                    if KedroFastApi == endpoint_type
                }

                if managed_endpoints:
                    compilation_specs_inputs = []
                    compilation_specs_outputs = []
                    compilation_specs_parameters = []

                    query_params = extract_query_params_from_endpoint(
                        app, route.path, list(route.methods)
                    )
                    for query_param in query_params:
                        compilation_specs_parameters.append(query_param["name"])

                    for (
                        param_name,
                        param_type,
                    ) in route.endpoint.__annotations__.items():
                        encapsuled_managed_type = [
                            type
                            for type in typing.get_args(param_type)
                            if type.__class__.__name__ == "ModelMetaclass"
                        ]
                        if encapsuled_managed_type:
                            if param_type.__name__ == "List":
                                managed_type = typing.get_args(param_type)[0]
                            else:
                                raise KedroFastApiSessionError(
                                    f"Only List type is authourized to encapsul a managed request body Data Model. We got {param_type} for {route.endpoint.__name__} endpoint"
                                )
                        else:
                            managed_type = param_type
                        if (
                            managed_type.__class__.__name__ == "ModelMetaclass"
                            and param_name == "return"
                        ):
                            compilation_specs_outputs.append(route.endpoint.__name__)

                        elif managed_type.__class__.__name__ == "ModelMetaclass":
                            compilation_specs_inputs.append(param_name)

                    if (
                        inspect.iscoroutinefunction(route.endpoint)
                        and compilation_specs_outputs
                    ):
                        LOGGER.warning(
                            f"We cannot declare {route.endpoint.__name__} endpoint as async while waiting reponse data from pipeline's {compilation_specs_outputs} outputs. We gonna switch to sync mode"
                        )

                    infer_artifacts = True
                    # If only the KedroFastpi dependency that are present in the endpoint annotations, we can disable infering artifacts as the service will be exclusively used as trigger for the pipeline
                    if len(route.endpoint.__annotations__) == 1:
                        infer_artifacts = False

                    compilation_specs.append(
                        CompilationSpec(
                            namespace=route.operation_id,
                            inputs=compilation_specs_inputs,
                            outputs=compilation_specs_outputs,
                            parameters=compilation_specs_parameters,
                            infer_artifacts=infer_artifacts,
                        )
                    )

        self.session.compile(compilation_specs=compilation_specs)


kedro_fastapi_session = KedroFastApiSession()
KedroFastApi = Annotated[dict, Depends(kedro_fastapi_session)]


class KedroFastApiSessionError(Exception):
    """Error raised in catalog rendering operations"""


def extract_query_params_from_endpoint(
    app: FastAPI, path: str, methods: typing.List[str]
):
    openapi_schema = app.openapi()
    paths = openapi_schema.get("paths", {})

    query_params = []

    path_item = paths.get(path, {})
    for method in methods:
        operation = path_item.get(method.lower(), {})
        parameters = operation.get("parameters", [])
        for param in parameters:
            if param["in"] == "query":
                query_params.append(param)

    return query_params
