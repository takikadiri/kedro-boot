from typing import Any, Dict, List
from pluggy import PluginManager
from kedro.runner import AbstractRunner, SequentialRunner
from kedro.pipeline import Pipeline
from kedro.io import DataCatalog


class KedroBootRunner:
    def __init__(
        self,
        hook_manager: PluginManager,
        session_id: str,
        runner: AbstractRunner = None,
    ) -> None:
        if runner and not isinstance(runner, AbstractRunner):
            raise KedroBootRunnerError(
                f"The runner parameter should be an AbstracRunner, {runner.__class__.__name__} given instead"
            )

        self.runner = runner or SequentialRunner()

        self._session_id = session_id
        self._hook_manager = hook_manager

    def run(
        self, pipeline: Pipeline, catalog: DataCatalog, outputs_datasets: List[str]
    ) -> Dict[str, Any]:
        self.runner.run(
            pipeline=pipeline,
            catalog=catalog,
            hook_manager=self._hook_manager,
            session_id=self._session_id,
        )

        print(catalog._data_sets)
        output_datasets = {}
        # if multiple outputs datasets, load the returned datasets indexed by pipeline view outputs
        if outputs_datasets and len(outputs_datasets) > 1:
            output_datasets = {
                dataset_name: catalog.load(dataset_name)
                for dataset_name in outputs_datasets
            }
        elif outputs_datasets and len(outputs_datasets) == 1:
            output_datasets = catalog.load(list(outputs_datasets)[0])
        # If no pipeline view outputs, load all the memorydatasets outputs
        else:
            print(catalog._data_sets)
            output_datasets = {
                dataset_name: catalog.load(dataset_name)
                for dataset_name in pipeline.outputs()
                if catalog._data_sets[dataset_name].__class__.__name__.lower()
                == "memorydataset"
            }
        return output_datasets


class KedroBootRunnerError(Exception):
    """Error raised in case of kedro boot runner error"""
