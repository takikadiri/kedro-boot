"""Helper functions for rendering catalogs using iteration datasets"""

import copy
import logging
from pathlib import PurePath
import re
from typing import Any, Dict, List, Union
from omegaconf import OmegaConf

from kedro.io import MemoryDataset

LOGGER = logging.getLogger(__name__)


def render_datasets(datasets: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore
    return {
        dataset_name: copy.deepcopy(dataset_value)
        for dataset_name, dataset_value in datasets.items()
    }


def render_template_datasets(
    catalog_templates: Dict[str, Any], iteration_template_params: dict
) -> Dict[str, Any]:  # type: ignore
    template_params = recursively_get_dataset_template_params(catalog_templates)
    remaining_catalog_tempate_params = set(template_params) - set(
        iteration_template_params
    )
    if remaining_catalog_tempate_params:
        LOGGER.warning(
            f"There is not enough given iteration template param to render all the Template expressions. Template expressions are {set(template_params)} and the actual given template params are {set(iteration_template_params)}. Default values will be used for {remaining_catalog_tempate_params}"
        )

    iteration_template_params_without_run_id = set(iteration_template_params) - {
        "run_id"
    }
    remaining_iteration_template_params = (
        iteration_template_params_without_run_id - set(template_params)
    )
    if remaining_iteration_template_params:
        LOGGER.warning(
            f"There is remaining iteration template params that are not used for rendering template expressions. Template expressions are {set(template_params)} and the actual given iteration template params are {iteration_template_params_without_run_id}. {remaining_iteration_template_params} are remaining unused"
        )

    rendered_datasets = {}
    for dataset_name, dataset_value in catalog_templates.items():
        rendered_dataset_value = copy.deepcopy(dataset_value)
        recursively_render_parametrized_dataset_template(
            rendered_dataset_value, iteration_template_params
        )
        rendered_datasets[dataset_name] = rendered_dataset_value

    return rendered_datasets


def render_parameter_datasets(
    catalog_parameters: Dict[str, Any], iteration_parameters: dict
) -> Dict[str, Any]:  # type: ignore
    formatted_iteration_params = {
        f"params:{param_name}": param_value
        for param_name, param_value in iteration_parameters.items()
    }
    if "parameters" in catalog_parameters and iteration_parameters:
        formatted_iteration_params.update({"parameters": iteration_parameters})

    remaining_catalog_params = set(catalog_parameters) - set(formatted_iteration_params)
    if remaining_catalog_params:
        LOGGER.warning(
            f"There are not enough given iteration parameters to render all the catalog parameters. Exposed Catalog parameters are {set(catalog_parameters)} and the actual given iteration parameters are {formatted_iteration_params}. {remaining_catalog_params} cannot be rendered"
        )

    # check remaining iteration parameters in case of having only parameters dataset
    if "parameters" in catalog_parameters and len(catalog_parameters) == 1:
        catalog_parameters_values = catalog_parameters.get("parameters").load()
        iteration_parameters_values = formatted_iteration_params.get("parameters", {})
        remaining_iteration_params = set(iteration_parameters_values) - set(
            catalog_parameters_values
        )
        if remaining_iteration_params:
            LOGGER.warning(
                f"There are remaining iteration parameters that are not used for rendering catalog parameters. Catalog parameters are {catalog_parameters_values} and the actual given iteration parameters are {iteration_parameters_values}. {remaining_iteration_params} are unused"
            )
    else:
        remaining_iteration_params = set(formatted_iteration_params) - set(
            catalog_parameters
        )
        if remaining_iteration_params:
            LOGGER.warning(
                f"There are remaining iteration parameters that are not used for rendering catalog parameters. Catalog parameters are {set(catalog_parameters)} and the actual given iteration parameters are {formatted_iteration_params}. {remaining_iteration_params} are unused"
            )

    rendered_datasets = {}

    for dataset_name, dataset_value in catalog_parameters.items():
        if formatted_iteration_params.get(dataset_name):
            rendered_dataset_value = copy.deepcopy(dataset_value)

            parameters = rendered_dataset_value.load()

            if isinstance(parameters, dict):
                rendered_datasets[dataset_name] = MemoryDataset(
                    _recursive_dict_update(
                        parameters, formatted_iteration_params.get(dataset_name)
                    )
                )
            else:
                rendered_datasets[dataset_name] = MemoryDataset(
                    formatted_iteration_params[dataset_name]
                )
        else:
            rendered_datasets[dataset_name] = dataset_value

    return rendered_datasets


def render_input_datasets(
    catalog_inputs: Dict[str, Any], iteration_inputs: dict
) -> Dict[str, Any]:  # type: ignore
    remaining_catalog_inputs = set(catalog_inputs) - set(iteration_inputs)

    if remaining_catalog_inputs:
        raise CatalogRendererError(
            f"There is not enough iteration inputs to render catalog inputs. Catalog inputs are {set(catalog_inputs)} and the actual given iteration inputs are {set(iteration_inputs)}. {remaining_catalog_inputs} are remaining"
        )

    remaining_iteration_inputs = set(iteration_inputs) - set(catalog_inputs)

    if remaining_iteration_inputs:
        LOGGER.warning(
            f"These iteration inputs datasets {remaining_iteration_inputs} are not used in rendering catalog inputs datasets. Catalog inputs are {set(catalog_inputs)} and the actual given iteration inputs are {set(iteration_inputs)}."
        )

    rendered_datasets = {}

    for dataset_name, dataset_value in catalog_inputs.items():
        LOGGER.info(f"Injecting '{dataset_name}' input into the catalog")
        rendered_dataset_value = copy.deepcopy(dataset_value)
        iteration_input_data = iteration_inputs[dataset_name]
        if "pandas" in str(rendered_dataset_value.__class__).lower() and (
            isinstance(iteration_input_data, dict)
            or (
                isinstance(iteration_input_data, list)
                and all(isinstance(item, dict) for item in iteration_input_data)
            )
        ):
            # Lazily import pandas. We expect user have pandas installed if they use pandas datasets
            import pandas as pd

            LOGGER.info(f"Converting '{dataset_name}' to pandas")
            rendered_dataset_value = MemoryDataset(
                pd.json_normalize(iteration_inputs[dataset_name])
            )
        else:
            rendered_dataset_value = MemoryDataset(iteration_inputs[dataset_name])
        rendered_datasets[dataset_name] = rendered_dataset_value

    return rendered_datasets


def recursively_render_template(
    dataset_attributes: Union[str, list, dict, PurePath], template_args: dict
) -> Union[None, str, list, dict, PurePath]:
    if isinstance(dataset_attributes, str):
        config = OmegaConf.create(
            {**{"dataset_entry": dataset_attributes}, **template_args}
        )
        return config.dataset_entry
        # return Template(
        #     dataset_attributes, variable_start_string="[[", variable_end_string="]]"
        # ).render(template_args)

    elif isinstance(dataset_attributes, PurePath):
        config = OmegaConf.create(
            {**{"dataset_entry": str(dataset_attributes)}, **template_args}
        )

        return PurePath(config.dataset_entry)

    elif isinstance(dataset_attributes, dict):
        for key in dataset_attributes:
            dataset_attributes[key] = recursively_render_template(
                dataset_attributes[key], template_args
            )
        return dataset_attributes

    elif isinstance(dataset_attributes, list):
        for i in range(len(dataset_attributes)):
            dataset_attributes[i] = recursively_render_template(
                dataset_attributes[i], template_args
            )
        return dataset_attributes

    else:
        return dataset_attributes


def recursively_render_parametrized_dataset_template(dataset: Any, template_args: dict):
    for attr, value in dataset.__dict__.items():
        setattr(dataset, attr, recursively_render_template(value, template_args))


def recursively_get_dataset_template_params(datasets: dict) -> List[str]:
    template_params = []
    for ds_value in datasets.values():
        for value in ds_value.__dict__.values():
            template_params.extend(recursively_get_template_params(value))
    return template_params


def recursively_get_template_params(
    dataset_attributes: Union[str, list, dict, PurePath],
) -> List[str]:
    if isinstance(dataset_attributes, str):
        config = OmegaConf.create({"dataset_entry": dataset_attributes})
        return list(find_config_interpolation_keys(config))
        # return list(meta.find_undeclared_variables(env.parse(dataset_attributes)))

    elif isinstance(dataset_attributes, PurePath):
        config = OmegaConf.create({"dataset_entry": str(dataset_attributes)})
        return list(find_config_interpolation_keys(config))

    elif isinstance(dataset_attributes, dict):
        template_params = []
        for key in dataset_attributes:
            template_params.extend(
                recursively_get_template_params(dataset_attributes[key])
            )
        return template_params

    elif isinstance(dataset_attributes, list):
        template_params = []
        for dataset_attribute in dataset_attributes:
            template_params.extend(recursively_get_template_params(dataset_attribute))
        return template_params

    else:
        return []


def _recursive_dict_update(original_dict, new_dict):
    for key, value in new_dict.items():
        if isinstance(value, dict):
            original_dict[key] = _recursive_dict_update(
                original_dict.get(key, {}), value
            )
        else:
            original_dict[key] = value
    return original_dict


def find_config_interpolation_keys(config):
    interpolation_keys = set()
    interpolation_pattern = re.compile(r"\$\{oc\.select\s*:\s*([^,\s]+)\s*,")

    def extract_keys(cfg):
        for key, value in cfg.items_ex(resolve=False):
            if isinstance(value, str):
                keys = [
                    match.group(1) for match in interpolation_pattern.finditer(value)
                ]
                interpolation_keys.update(keys)
            elif OmegaConf.is_config(value):
                extract_keys(value)

    extract_keys(config)
    return interpolation_keys


class CatalogRendererError(Exception):
    """Error raised in catalog rendering operations"""
