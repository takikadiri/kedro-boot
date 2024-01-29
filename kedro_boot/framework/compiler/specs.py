"""This module implements CompilationSpec and the logic of namespacing and dataset's naming."""

from typing import List
from kedro.pipeline import Pipeline


class CompilationSpec:
    """``NamespaceSpec`` is a user facing interface that encapsulate catalog compilation spec's attributes and utilities"""

    def __init__(
        self,
        namespace: str = None,
        inputs: List[str] = None,
        outputs: List[str] = None,
        parameters: List[str] = None,
        infer_artifacts: bool = True,
    ) -> None:
        """Init the ``CompilationSpec``.

        Args:
            namespace (str): pipeline's namespace
            inputs (List[str]): inputs datasets to be exposed to the App. Specify it without the namespace prefix
            namespace (List[str]): outputs datasets to be exposed to the App. Specify it without the namespace prefix
            namespace (List[str]): parameters datasets to be exposed to the App. Specify it without the namespace prefix
            infer_artifacts (bool): Wheter if the compiler infer artifacts datasets. Default to True
        """
        self._namespace = namespace
        infer_artifacts = infer_artifacts if infer_artifacts is not None else True
        self._spec = dict(
            inputs=inputs or [],
            outputs=outputs or [],
            parameters=parameters or [],
            infer_artifacts=infer_artifacts,
        )

    @property
    def namespace(self) -> str:
        return self._namespace

    @namespace.setter
    def namespace(self, value: str) -> None:
        self._namespace = value

    @property
    def inputs(self) -> List[str]:
        return self._spec["inputs"]

    @inputs.setter
    def inputs(self, value: List[str]) -> None:
        self._spec["inputs"] = value

    @property
    def namespaced_inputs(self) -> List[str]:
        return namespace_datasets_names(self.inputs, self._namespace)

    @property
    def outputs(self) -> List[str]:
        return self._spec["outputs"]

    @property
    def namespaced_outputs(self) -> List[str]:
        return namespace_datasets_names(self.outputs, self._namespace)

    @outputs.setter
    def outputs(self, value: List[str]) -> None:
        self._spec["outputs"] = value

    @property
    def parameters(self) -> List[str]:
        return self._spec["parameters"]

    @property
    def namespaced_parameters(self) -> List[str]:
        return namespace_datasets_names(self.parameters, self._namespace)

    @property
    def prefixed_namespaced_parameters(self) -> List[str]:
        return [f"params:{param}" for param in self.namespaced_parameters]

    @parameters.setter
    def parameters(self, value: List[str]) -> None:
        self._spec["parameters"] = value

    @property
    def infer_artifacts(self) -> bool:
        return self._spec["infer_artifacts"]

    @infer_artifacts.setter
    def infer_artifacts(self, value: bool) -> None:
        self._spec["infer_artifacts"] = value

    def to_dict(self) -> dict:
        return dict(namespace=self._namespace, specs=self._specs)

    @classmethod
    def infer_compilation_specs(cls, pipeline: Pipeline):
        """Infer Compilation specs from a pipeline.

        Args:
            pipeline (Pipeline): kedro pipeline
        Returns:
            List[CompilationSpec]: compilation specs
        """

        namespaces = set()
        for node in pipeline.nodes:
            namespaces.add(node.namespace)

        compilation_specs = []

        for namespace in namespaces:
            compilation_spec = CompilationSpec(namespace=namespace)
            namespace_pipeline = filter_pipeline(pipeline, namespace)
            for dataset_name in namespace_pipeline.inputs():
                if not namespace and "params:" in dataset_name:
                    compilation_spec.parameters.append(
                        dataset_name.replace("params:", "")
                    )
                elif f"params:{namespace}." in dataset_name:
                    compilation_spec.parameters.append(
                        dataset_name.replace(f"params:{namespace}.", "")
                    )
                elif f"{namespace}." in dataset_name:
                    compilation_spec.inputs.append(
                        dataset_name.replace(f"{namespace}.", "")
                    )

            for dataset_name in namespace_pipeline.outputs():
                if f"{namespace}." in dataset_name:
                    compilation_spec.outputs.append(
                        dataset_name.replace(f"{namespace}.", "")
                    )

            compilation_specs.append(compilation_spec)

        return compilation_specs


def namespace_datasets_names(datasets_names: list, namespace: str) -> List[str]:
    namespaced_datasets_names = []
    for dataset_name in datasets_names:
        namespaced_dataset_name = namespace_dataset_name(dataset_name, namespace)
        namespaced_datasets_names.append(namespaced_dataset_name)

    return namespaced_datasets_names


def namespace_dataset_name(dataset_name: str, namespace: str) -> str:
    if namespace:
        return f"{namespace}.{dataset_name}"

    return dataset_name


def filter_pipeline(pipeline: Pipeline, namespace: str) -> Pipeline:
    # Replace the pipeline.only_nodes_with_namespaces as it does not take None namespace.
    nodes = []
    for n in pipeline.nodes:
        if str(n.namespace) == str(namespace):
            nodes.append(n)

    return Pipeline(nodes)
