"""Helper functions for compiling catalog_views's datasets"""

import logging
from pathlib import PurePath
from typing import Any, Dict, Union
from omegaconf import OmegaConf

from kedro.io import MemoryDataSet

from kedro_boot.pipeline.pipeline import PipelineView

from .view import CatalogView

LOGGER = logging.getLogger(__name__)


def compile_with_pipeline_inputs(
    catalog_view: CatalogView,
    pipeline_inputs: Dict[
        str, Any
    ],  # Any is AbstractDataSet, for retrocompatibility reasons we don't specify the type as it was renamed lately to AbstractDataset
    pipeline_view: PipelineView,
) -> None:
    """Build catalog views's datasets using pipeline view dataset categories and pipeline inputs.
    Each dataset category (inputs, parameters, templates, artifacts, unmanaged) could be filled through this process.

    Args:
        catalog_view (CatalogView): object to be Build through the compilation process
        pipeline_inputs (dict): pipeline inputs as the datasets to be used for building the catalog_view
        pipeline_view (PipelineView): Contains the dataset names that belong to each category, plus some compilation options (infer artifacts, infer templates)
    """
    for dataset_name, dataset_value in pipeline_inputs.items():
        # inputs
        if dataset_name in pipeline_view.inputs:
            catalog_view.inputs[dataset_name] = dataset_value

        # parameters
        elif _check_if_dataset_is_param(
            dataset_name=dataset_name, pipeline_view_parameters=pipeline_view.parameters
        ):
            catalog_view.parameters[dataset_name] = dataset_value

        # templates
        elif recursively_check_dataset_parametrized_values(dataset_value):
            catalog_view.templates[dataset_name] = dataset_value

        # artifacts
        elif dataset_name in pipeline_view.artifacts:
            LOGGER.info(f"Loading {dataset_name} dataset as a MemoryDataset")
            catalog_view.artifacts[dataset_name] = MemoryDataSet(
                dataset_value.load(), copy_mode="assign"
            )

        elif pipeline_view.infer_artifacts:
            if pipeline_view.inputs:
                LOGGER.info(
                    f"Infered artifact dataset {dataset_name}. Loading it as a MemoryDataset"
                )
                catalog_view.artifacts[dataset_name] = MemoryDataSet(
                    dataset_value.load(), copy_mode="assign"
                )
            else:
                catalog_view.unmanaged[dataset_name] = dataset_value

        # Others
        else:
            catalog_view.unmanaged[dataset_name] = dataset_value


def compile_with_all_pipeline_outputs(
    catalog_view: CatalogView,
    all_pipeline_outputs: Dict[
        str, Any
    ],  # Any is AbstractDataSet, for retrocompatibility reasons we don't specify the type as it was renamed lately to AbstractDataset
    pipeline_view: PipelineView,
) -> None:
    """Build catalog views's datasets using pipeline view dataset categories and all pipeline outputs.
    Each dataset category (inputs, parameters, templates, artifacts, unmanaged) could be filled through this process.

    Args:
        catalog_view (CatalogView): object to be Build through the compilation process
        all_pipeline_outputs (dict): all the pipeline outputs as the datasets to be used for building the catalog_view
        pipeline_view (PipelineView): Contains the dataset names that belong to each category, plus some compilation options (infer artifacts, infer templates)
    """

    for dataset_name, dataset_value in all_pipeline_outputs.items():
        is_template_dataset = recursively_check_dataset_parametrized_values(
            dataset_value
        )

        if dataset_name in pipeline_view.outputs:
            if dataset_value.__class__.__name__.lower() != "memorydataset":
                LOGGER.warning(
                    f"This pipeline output '{dataset_name}' will cost you an I/O operation, please consider freeing it (making it a MemoryDataSet)."
                )

            catalog_view.outputs[dataset_name] = dataset_value

            if is_template_dataset:
                catalog_view.templates[dataset_name] = dataset_value

        else:
            if (
                dataset_value.__class__.__name__.lower() != "memorydataset"
                and pipeline_view.outputs
            ):
                LOGGER.warning(
                    f"This pipeline output '{dataset_name}' will cost you an I/O operation without being used by current app, please consider freeing it. the pipeline outputs that are needed by the current pipeline view ({catalog_view.name}) are : {pipeline_view.outputs}"
                )
            if is_template_dataset:
                catalog_view.templates[dataset_name] = dataset_value
            else:
                catalog_view.unmanaged[dataset_name] = dataset_value


def recursively_check_parametrized_values(
    dataset_attributes: Union[str, list, dict, PurePath]
) -> bool:  # noqa: PLR0911
    """Helper that check if any of the dataset attributes is parametrized (contains ${oc.select:param_name,default_value})

    Args:
        dataset (Any): Any kedro dataset

    Returns:
        bool: _description_
    """
    if isinstance(dataset_attributes, str):
        config = OmegaConf.create({"dataset_entry": dataset_attributes})
        return OmegaConf.is_interpolation(config, "dataset_entry")
        # return bool(re.search(r"\[\[.*?\]\]", dataset_attributes))

    elif isinstance(dataset_attributes, PurePath):
        config = OmegaConf.create({"dataset_entry": str(dataset_attributes)})
        return OmegaConf.is_interpolation(config, "dataset_entry")

    elif isinstance(dataset_attributes, dict):
        for key in dataset_attributes:
            if recursively_check_parametrized_values(dataset_attributes[key]):
                return True
        return False

    elif isinstance(dataset_attributes, list):
        for i in range(len(dataset_attributes)):
            if recursively_check_parametrized_values(dataset_attributes[i]):
                return True
        return False

    else:
        return False


def recursively_check_dataset_parametrized_values(dataset: Any) -> bool:
    """Helper that check if any of the dataset attributes is parametrized (contains [[...]])

    Args:
        dataset (Any): Any kedro dataset

    Returns:
        bool: _description_
    """
    for value in dataset.__dict__.values():
        if recursively_check_parametrized_values(value):
            return True
    return False


def _check_if_dataset_is_param(dataset_name, pipeline_view_parameters) -> bool:
    """Helper that extract the dataset name from the params:... or parameters:... string

    Args:
        dataset_name (str): dataset name

    Returns:
        str: dataset name without params: or parameters: prefix
    """
    if dataset_name == "parameters":
        return True
    elif "params:" in dataset_name:
        return dataset_name.split("params:")[1] in pipeline_view_parameters
    else:
        return False


class CatalogCompilerError(Exception):
    """Error raised in AppCatalog compilation process"""
