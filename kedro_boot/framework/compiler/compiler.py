"""Helper functions for compiling kedro catalog"""

import logging
from pathlib import PurePath
from typing import Any, Dict, Optional, Union
from omegaconf import OmegaConf
from kedro.io import AbstractDataset

from .specs import CompilationSpec

LOGGER = logging.getLogger(__name__)


class CatalogAssembly:
    """``CatalogAssembly`` is the resulting object of the catalog compilation process"""

    def __init__(
        self,
        inputs: Optional[dict] = None,
        outputs: Optional[dict] = None,
        parameters: Optional[dict] = None,
        artifacts: Optional[dict] = None,
        templates: Optional[dict] = None,
        unmanaged: Optional[dict] = None,
    ) -> None:
        """Init ``CatalogView`` with a name and a categorisation of the datasets that are exposed to the app.

        Args:
            inputs dict: Inputs datasets that will be injected by the app data at iteration time.
            outputs dict: Outputs dataset that hold the iteration run results.
            parameters dict: Parameters that will be injected by the app data at iteration time.
            artifacts dict: Artifacts datasets that will be materialized (loaded as MemoryDataset) at startup time.
            templates dict: Templates datasets that contains jinja expressions in this form [[ expressions ]].
            unmanaged dict: Datasets that will not undergo any operation and keeped as is
        """

        self.inputs = inputs or {}
        self.outputs = outputs or {}
        self.artifacts = artifacts or {}
        self.templates = templates or {}
        self.parameters = parameters or {}
        self.unmanaged = unmanaged or {}

    def __add__(self, catalog_assembly):
        return CatalogAssembly(
            inputs={**self.inputs, **catalog_assembly.inputs},
            outputs={**self.outputs, **catalog_assembly.outputs},
            artifacts={**self.artifacts, **catalog_assembly.artifacts},
            parameters={**self.parameters, **catalog_assembly.parameters},
            templates={**self.templates, **catalog_assembly.templates},
            unmanaged={**self.unmanaged, **catalog_assembly.unmanaged},
        )


def compile_with_pipeline_inputs(
    pipeline_inputs: Dict[
        str, Any
    ],  # Any is AbstractDataSet, for retrocompatibility reasons we don't specify the type as it was renamed lately to AbstractDataset
    compilation_spec: CompilationSpec,
) -> CatalogAssembly:
    """Compile a CatalogAssembly using pipeline's inputs datasets and following the compilation specs.

    Args:
        pipeline_inputs (dict): pipeline's inputs datasets
        compilation_spec (CompilationSpec):
    """

    catalog_assembly = CatalogAssembly()

    for dataset_name, dataset_value in pipeline_inputs.items():
        # inputs
        if dataset_name in compilation_spec.namespaced_inputs:
            catalog_assembly.inputs[dataset_name] = dataset_value

        # parameters
        elif _check_if_dataset_is_param(
            dataset_name=dataset_name,
            specs_parameters=compilation_spec.namespaced_parameters,
        ):
            catalog_assembly.parameters[dataset_name] = dataset_value

        # templates
        elif recursively_check_dataset_parametrized_values(dataset_value):
            catalog_assembly.templates[dataset_name] = dataset_value

        elif compilation_spec.infer_artifacts:
            catalog_assembly.artifacts[dataset_name] = dataset_value
        # Others
        else:
            catalog_assembly.unmanaged[dataset_name] = dataset_value

    return catalog_assembly


def compile_with_all_pipeline_outputs(
    all_pipeline_outputs: Dict[
        str, AbstractDataset
    ],  # Any is AbstractDataSet, for retrocompatibility reasons we don't specify the type as it was renamed lately to AbstractDataset
    compilation_spec: CompilationSpec,
) -> CatalogAssembly:
    """Compile a CatalogAssembly using all pipeline's outputs datasets and following the compilation specs.

    Args:
        pipeline_inputs (dict): pipeline's inputs datasets
        compilation_spec (CompilationSpec):
    """

    catalog_assembly = CatalogAssembly()

    for dataset_name, dataset_value in all_pipeline_outputs.items():
        is_template_dataset = recursively_check_dataset_parametrized_values(
            dataset_value
        )

        if dataset_name in compilation_spec.namespaced_outputs:
            if dataset_value.__class__.__name__.lower() != "memorydataset":
                LOGGER.warning(
                    f"This pipeline output '{dataset_name}' will cost you an I/O operation, please consider freeing it (making it a MemoryDataset)."
                )

            catalog_assembly.outputs[dataset_name] = dataset_value

            if is_template_dataset:
                catalog_assembly.templates[dataset_name] = dataset_value

        else:
            if (
                dataset_value.__class__.__name__.lower() != "memorydataset"
                and compilation_spec.namespaced_outputs
            ):
                LOGGER.warning(
                    f"This pipeline output '{dataset_name}' will cost you an I/O operation without being used by current app, please consider freeing it. the pipeline outputs that are needed by the current pipeline namespace ({compilation_spec.namespace}) are : {compilation_spec.namespaced_outputs}"
                )
            if is_template_dataset:
                catalog_assembly.templates[dataset_name] = dataset_value
            else:
                catalog_assembly.unmanaged[dataset_name] = dataset_value

    return catalog_assembly


def recursively_check_parametrized_values(
    dataset_attributes: Union[str, list, dict, PurePath],
) -> bool:  # noqa: PLR0911
    """Helper that check if any of the dataset attributes is parametrized

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
    """Helper that check if any of the dataset attributes is parametrized

    Args:
        dataset (Any): Any kedro dataset

    Returns:
        bool: _description_
    """
    for value in dataset.__dict__.values():
        if recursively_check_parametrized_values(value):
            return True
    return False


def _check_if_dataset_is_param(dataset_name, specs_parameters) -> bool:
    """Helper that extract the dataset name from the params:... or parameters:... string

    Args:
        dataset_name (str): dataset name

    Returns:
        str: dataset name without params: or parameters: prefix
    """
    if dataset_name == "parameters":
        return True
    elif "params:" in dataset_name:
        return dataset_name.split("params:")[1] in specs_parameters
    else:
        return False


class CatalogCompilerError(Exception):
    """Error raised in catalog compilation process"""
