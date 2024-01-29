""""``KedroBootContext`` provides context for the kedro boot project."""
import logging
from typing import List, Optional, Tuple

from kedro.io import DataCatalog

from kedro.pipeline.pipeline import Pipeline
from kedro.io import MemoryDataset
from kedro_boot.utils import find_duplicates

from kedro_boot.framework.compiler.compiler import (
    compile_with_all_pipeline_outputs,
    compile_with_pipeline_inputs,
)
from kedro_boot.framework.renderer.renderer import (
    render_datasets,
    render_input_datasets,
    render_parameter_datasets,
    render_template_datasets,
)
from kedro_boot.framework.compiler.specs import (
    CompilationSpec,
    filter_pipeline,
    namespace_dataset_name,
)

LOGGER = logging.getLogger(__name__)


class KedroBootContext:
    """ "``KedroBootContext`` Manage and hold main Kedro Boot objects."""

    def __init__(self, pipeline: Pipeline, catalog: DataCatalog) -> None:
        """Init the ``KedroBootContext`` with the base kedro pipeline and catalog.

        Args:
            catalog (DataCatalog): Kedro Catalog
        """
        self.pipeline = pipeline
        self.catalog = catalog

        self._namespaces_registry = {}

    def compile(self, compilation_specs: List[CompilationSpec] = None) -> None:
        """Prepare kedro's resources for iteration time by creating a namespace registry indexed by namespaces that contains the corresponding pipelines and catalogs pré-materialized and organized by dataset categories according to their relevance to the application

        Args:
            compilation_specs (List[CompilationSpec]): Compilation Specs provided by the App. compilation_specs are infered from the pipeline if no compilation_specs provided.
        """

        infered_compilation_specs = CompilationSpec.infer_compilation_specs(
            self.pipeline
        )

        if compilation_specs:
            # check if the given namespaces specs have duplicate namespaces
            namespaces = [
                compilation_spec.namespace for compilation_spec in compilation_specs
            ]
            duplicated_namespaces = find_duplicates(namespaces)
            if duplicated_namespaces:
                raise ValueError(
                    f"Cannot compile the catalog with these duplicated namespace names: '{duplicated_namespaces}'"
                )

            # check if the given namespaces inline with the pipeline namespaces
            given_namespaces = set(namespaces)
            infered_namespaces = set(
                [
                    compilation_spec.namespace
                    for compilation_spec in infered_compilation_specs
                ]
            )

            if given_namespaces != infered_namespaces:
                LOGGER.warning(
                    f"The given namespaces does not match with the pipeline namespaces. pipeline namespace are {infered_namespaces}, and the given namespaces are {given_namespaces}"
                )

        else:
            LOGGER.info(
                "No namespace specs provided by the app, we gonna infer them from pipeline namespaces"
            )
            compilation_specs = infered_compilation_specs

        for compilation_spec in compilation_specs:
            pipeline = filter_pipeline(
                pipeline=self.pipeline, namespace=compilation_spec.namespace
            )

            pipeline_inputs = {
                dataset_name: self.catalog._get_dataset(dataset_name)
                for dataset_name in pipeline.inputs()
            }

            remaining_inputs_specs = set(compilation_spec.namespaced_inputs) - set(
                pipeline_inputs.keys()
            )
            if remaining_inputs_specs:
                raise KedroBootContextError(
                    f"These inputs datasets {remaining_inputs_specs} given for {compilation_spec.namespace} spec, does not exists in pipeline inputs."
                )

            remaining_parameters_specs = set(
                compilation_spec.prefixed_namespaced_parameters
            ) - set(pipeline_inputs.keys())
            if remaining_parameters_specs:
                raise KedroBootContextError(
                    f"These parameters datasets {remaining_parameters_specs} given in {compilation_spec.namespace} namespace specs, does not exists in pipeline parameters."
                )

            catalog_assembly_with_inputs = compile_with_pipeline_inputs(
                pipeline_inputs=pipeline_inputs,
                compilation_spec=compilation_spec,
            )

            all_pipeline_outputs = {
                dataset_name: self.catalog._get_dataset(dataset_name)
                for dataset_name in pipeline.all_outputs()
            }

            remaining_outputs_specs = set(compilation_spec.namespaced_outputs) - set(
                all_pipeline_outputs.keys()
            )
            if remaining_outputs_specs:
                raise KedroBootContextError(
                    f"These outputs datasets {remaining_outputs_specs} given for {compilation_spec.namespace} spec, does not exists in pipeline outputs."
                )

            catalog_assembly_with_all_outputs = compile_with_all_pipeline_outputs(
                all_pipeline_outputs=all_pipeline_outputs,
                compilation_spec=compilation_spec,
            )

            catalog_assembly = (
                catalog_assembly_with_inputs + catalog_assembly_with_all_outputs
            )

            LOGGER.info(
                "catalog compilation completed for the namespace '%s'. Here is the report:\n"
                "  - Input datasets to be replaced/rendered at iteration time: %s\n"
                "  - Output datasets that hold the results of a run at iteration time: %s \n"
                "  - Parameter datasets to be replaced/rendered at iteration time: %s\n"
                "  - Artifact datasets to be materialized (preloader as memory dataset) at compile time: %s\n"
                "  - Template datasets to be rendered at iteration time: %s\n",
                compilation_spec.namespace,
                set(catalog_assembly.inputs),
                set(catalog_assembly.outputs),
                set(catalog_assembly.parameters),
                set(catalog_assembly.artifacts),
                set(catalog_assembly.templates),
            )

            self._namespaces_registry[compilation_spec.namespace] = dict(
                pipeline=pipeline,
                catalog=catalog_assembly,
                outputs=compilation_spec.namespaced_outputs,
            )

        LOGGER.info("Loading artifacts datasets as MemoryDataset ...")
        self.materialize_artifacts()

        LOGGER.info("Catalog compilation completed.")

    def materialize_artifacts(self):
        # Materialize the artifact dataset by loading them as memory in the compilation process. Here we merge all the artifact datasets (cross namespaces) so we can load once an artifact that is shared between two dataset in two different namespaces
        all_artifacts_datasets = {}
        # Merge all artifact datasets cross namespaces/specs
        for namespace in self._namespaces_registry.values():
            all_artifacts_datasets.update(namespace["catalog"].artifacts)

        # Materialized thoses artifact datasets in all_materialized_artifact_datasets
        all_materialized_artifact_datasets = {}
        for dataset_name, dataset_value in all_artifacts_datasets.items():
            LOGGER.info(f"Loading {dataset_name} as a MemoryDataset")
            all_materialized_artifact_datasets[
                dataset_name
            ] = MemoryDataset(  # Add Logging fro this operation
                dataset_value.load(), copy_mode="assign"
            )

        # Assign the materialized artifact back to namespace/spec artifact datasets
        for namespace in self._namespaces_registry.values():
            for dataset_name in namespace["catalog"].artifacts:
                namespace["catalog"].artifacts[
                    dataset_name
                ] = all_materialized_artifact_datasets[dataset_name]

    def render(
        self,
        namespace: str = None,
        inputs: Optional[dict] = None,
        parameters: Optional[dict] = None,
        itertime_params: Optional[dict] = None,
    ) -> Tuple[Pipeline, DataCatalog]:
        """Generate a (pipeline, catalog) by rendering a namespace registry using the provided App Data.

        Args:
            namespace (str): pipeline's namespace.
            inputs (dict): App inputs datasets that will be injected into the catalog.
            parameters (dict): App parameters datasets that will be injected into the catalog.
            itertime_params (dict): App itertime params that will resolve the itertime_params resolvers.

        Returns:
            Pipeline, DataCatalog: The rendered catalog
        """

        if namespace not in self._namespaces_registry:
            raise KedroBootContextError(
                f"The given {namespace} namespace is not present in the current selected pipeline"
            )

        inputs = inputs or {}
        parameters = parameters or {}
        itertime_params = itertime_params or {}

        namespaced_inputs = namespace_datasets(inputs, namespace)
        namespaced_parameters = namespace_datasets(parameters, namespace)

        catalog_assembly = self._namespaces_registry.get(namespace).get("catalog")

        rendered_catalog = DataCatalog()

        # Render each part of the catalog view
        input_datasets = render_input_datasets(
            catalog_inputs=catalog_assembly.inputs, iteration_inputs=namespaced_inputs
        )
        artifact_datasets = catalog_assembly.artifacts
        template_datasets = render_template_datasets(
            catalog_templates=catalog_assembly.templates,
            iteration_template_params=itertime_params,
        )
        parameter_datasets = render_parameter_datasets(
            catalog_parameters=catalog_assembly.parameters,
            iteration_parameters=namespaced_parameters,
        )
        output_datasets = render_datasets(datasets=catalog_assembly.outputs)
        unmanaged_datasets = render_datasets(datasets=catalog_assembly.unmanaged)

        rendered_catalog.add_all(
            {
                **input_datasets,
                **output_datasets,
                **parameter_datasets,
                **template_datasets,
                **artifact_datasets,
                **unmanaged_datasets,
            }
        )

        pipeline = self._namespaces_registry.get(namespace).get("pipeline")

        return pipeline, rendered_catalog

    def get_outputs_datasets(self, namespace: str) -> List[str]:
        return self._namespaces_registry.get(namespace).get("outputs")


def namespace_datasets(iteration_datasets: dict, namespace: str = None) -> dict:
    """namespacing the given app datasets
    Args:
        iteration_datasets (dict): datasets given by the ap at iteration time
        namespace (str): pipeline's namespace

    Returns:
        dict: namespaced_itretaion_datasets
    """

    namespaced_datasets = {}

    for dataset_name, dataset_value in iteration_datasets.items():
        namespaced_dataset_name = namespace_dataset_name(dataset_name, namespace)

        namespaced_datasets[namespaced_dataset_name] = dataset_value

    return namespaced_datasets


class KedroBootContextError(Exception):
    """Error raised in AppCatalog operations"""
