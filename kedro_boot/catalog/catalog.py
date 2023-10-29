""""``AppCatalog`` make the the kedro catalog ready for interaction with the kedro boot app."""
import copy
import logging
from typing import List, Optional

from kedro.io import DataCatalog

from kedro_boot.pipeline import AppPipeline

from .compiler import compile_with_all_pipeline_outputs, compile_with_pipeline_inputs
from .renderer import (
    render_datasets,
    render_input_datasets,
    render_parameter_datasets,
    render_template_datasets,
)
from .view import CatalogView

LOGGER = logging.getLogger(__name__)


class AppCatalog:
    """ "``AppCatalog`` Manage the kedro catalog lifecycle.
    At compilation time : It build a ``CatalogView`` for each ``PipelineView`` .
    At iteration time: catalog views are rendered/merged with data provided by the app
    """

    def __init__(self, catalog: DataCatalog) -> None:
        """Init the ``AppCatalog`` with the base kedro catalog.

        Args:
            catalog (DataCatalog): Kedro Catalog
        """
        self.catalog = catalog
        self.catalog_views = []

    def compile(self, app_pipeline: AppPipeline) -> None:
        """Build catalog view for each pipeline view.

        Args:
            app_pipeline (AppPipeline): Base pipeline with views defining datasets's categories and compilation options
        """

        for pipeline_view in app_pipeline.views:
            pipeline = app_pipeline.only_nodes_with_tags(pipeline_view.name)

            catalog_view = CatalogView(name=pipeline_view.name)

            pipeline_inputs = {
                dataset_name: self.catalog._data_sets[dataset_name]
                for dataset_name in pipeline.inputs()
            }
            print(pipeline_inputs)
            compile_with_pipeline_inputs(
                catalog_view=catalog_view,
                pipeline_inputs=pipeline_inputs,
                pipeline_view=pipeline_view,
            )

            # pipeline_outputs = {dataset_name: self.catalog._data_sets[dataset_name] for dataset_name in pipeline.outputs()}
            # print(pipeline_outputs)
            # compile_with_pipeline_outputs(
            #     catalog_view=catalog_view,
            #     pipeline_outputs=pipeline_outputs,
            #     pipeline_view=pipeline_view,
            # )

            # pipeline_intermediary = {dataset_name: self.catalog._data_sets[dataset_name] for dataset_name in pipeline.all_inputs() & pipeline.all_outputs()}
            # print(pipeline_intermediary)
            # compile_with_pipeline_intermediary(
            #     catalog_view=catalog_view,
            #     pipeline_intermediary=pipeline_intermediary,
            #     pipeline_view=pipeline_view,
            # )

            all_pipeline_outputs = {
                dataset_name: self.catalog._data_sets[dataset_name]
                for dataset_name in pipeline.all_outputs()
            }
            print(all_pipeline_outputs)
            compile_with_all_pipeline_outputs(
                catalog_view=catalog_view,
                all_pipeline_outputs=all_pipeline_outputs,
                pipeline_view=pipeline_view,
            )

            self.catalog_views.append(catalog_view)

            # if not catalog_view.outputs:
            #     LOGGER.warning(
            #         f"No output datasets were given for the current pipeline namespace '{catalog_view.namespace}'. We gonna return all free pipeline outputs"
            #     )

            LOGGER.info(
                "catalog compilation completed for the pipeline view '%s'. Here is the report:\n"
                "  - Input datasets to be replaced/rendered at iteration time: %s\n"
                "  - Output datasets that hold the results of a run at iteration time: %s \n"
                "  - Parameter datasets to be replaced/rendered at iteration time: %s\n"
                "  - Artifact datasets to be materialized (preloader as memory dataset) at startup time: %s\n"
                "  - Template datasets to be rendered at iteration time: %s\n",
                catalog_view.name,
                set(catalog_view.inputs),
                set(catalog_view.outputs),
                set(catalog_view.parameters),
                set(catalog_view.artifacts),
                set(catalog_view.templates),
            )

        LOGGER.info("Catalog compilation completed.")

    # def render(self, name: str, inputs: dict | None = None, outputs: dict | None = None, parameters: dict | None = None, templates: dict | None = None, artifacts: dict | None = None) -> DataCatalog:
    def render(
        self,
        name: str,
        inputs: Optional[dict] = None,
        parameters: Optional[dict] = None,
        template_params: Optional[dict] = None,
    ) -> DataCatalog:
        """Generate a catalog for a specific view by rendering the catalog view using app data.

        Args:
            name (str): catalog view name
            inputs (dict): inputs data given by the app
            parameters (dict): parameters data given by the app
            template_params (dict): template_params data given by the app

        Returns:
            DataCatalog: The rendered catalog
        """

        catalog_view = self.get_catalog_view(name)

        inputs = inputs or {}
        parameters = parameters or {}
        template_params = template_params or {}

        # namespacing inputs and parameters if needed to hopefully match the catalog. Users can give data without specifying namespace
        # TODO : we should add/infer namespace attribute to pipeline/catalog view, and consistently use it to namespace datasets. This actual namespacing is just a best effort
        namespaced_inputs = namespacing_datasets(inputs, catalog_view.inputs)
        namespaced_parameters = namespacing_datasets(
            parameters, catalog_view.parameters
        )

        rendered_catalog = DataCatalog()

        # Render each part of the catalog view
        input_datasets = render_input_datasets(
            catalog_view_inputs=catalog_view.inputs, iteration_inputs=namespaced_inputs
        )
        artifact_datasets = catalog_view.artifacts
        template_datasets = render_template_datasets(
            catalog_view_templates=catalog_view.templates,
            iteration_template_params=template_params,
        )
        parameter_datasets = render_parameter_datasets(
            catalog_view_parameters=catalog_view.parameters,
            iteration_parameters=namespaced_parameters,
        )
        output_datasets = render_datasets(datasets=catalog_view.outputs)
        unmanaged_datasets = render_datasets(datasets=catalog_view.unmanaged)

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

        return rendered_catalog

    def get_catalog_view(self, name: str) -> CatalogView:
        catalog_view = next(
            (
                catalog_view
                for catalog_view in self.catalog_views
                if catalog_view.name == name
            ),
            None,
        )

        if not catalog_view:
            raise AppCatalogError(
                f"The given catalog view '{name}' is not present in the catalog."
            )

        return catalog_view

    def get_view_names(self) -> List[str]:
        return [catalog_view.name for catalog_view in self.catalog_views]


def namespacing_datasets(iteration_datasets, catalog_dataset_names) -> dict:
    """namespacing the given app datasets if needed to hopefully match the catalog.
    Users can give data without specifying namespaces

    Args:
        iteration_datasets (_type_): datasets given by the ap at iteration time
        catalog_dataset_names (_type_): catalog dataset names

    Returns:
        dict: namespaced_itretaion_datasets
    """

    # Create a shallow copy as we'll potentially alterate some keys
    namespaced_iteration_datasets = copy.copy(iteration_datasets)

    # get remaining iteration datasets that are not in the catalog
    remaining_iteration_datasets = set(namespaced_iteration_datasets) - set(
        catalog_dataset_names
    )

    # Trying to namespace the remaining datasets to hopefully match the catalog
    if remaining_iteration_datasets:
        # Getting potentially namespaced datasets from the catalog
        only_namespaced_dataset_names = {
            catalog_dataset_name.split(".")[1]: catalog_dataset_name.split(".")[0]
            for catalog_dataset_name in catalog_dataset_names
            if len(catalog_dataset_name.split(".")) > 1
        }

        for dataset_name in remaining_iteration_datasets:
            if dataset_name in only_namespaced_dataset_names:
                namespace = only_namespaced_dataset_names[dataset_name].replace(
                    "params:", ""
                )
                LOGGER.info(f"Trying to namespace {dataset_name} with {namespace}")
                namespaced_dataset_name = f"{namespace}.{dataset_name}"
                # Replace dataset_name with namepace.dataset_name
                namespaced_iteration_datasets[
                    namespaced_dataset_name
                ] = namespaced_iteration_datasets.pop(dataset_name)

    return namespaced_iteration_datasets


class AppCatalogError(Exception):
    """Error raised in AppCatalog operations"""
