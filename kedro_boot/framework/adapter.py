"""``KedroBootAdapter`` transform a Kedro Session Run to a booting process."""
import logging
from typing import Any, Optional, Union

from kedro.config import ConfigLoader
from kedro.framework.hooks.manager import _NullPluginManager
from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline
from kedro.runner import AbstractRunner
from pluggy import PluginManager

from kedro_boot.app import AbstractKedroBootApp

LOGGER = logging.getLogger(__name__)


class KedroBootAdapter(AbstractRunner):
    """``KedroBootRunner`` transform a Kedro Session Run to a booting process."""

    def __init__(
        self,
        app: AbstractKedroBootApp,
        config_loader: ConfigLoader,
        app_run_args: Optional[dict] = None,
    ):
        """Instantiate the kedro boot adapter

        Args:
            app (AbstractKedroBootApp): Kedro Boot App object
            config_loader (OmegaConfigLoader): kedro config loader
            app_run_args (dict): App runtime args given by App CLI
        """

        super().__init__()

        self._app = app
        self._config_loader = config_loader
        self._app_run_args = app_run_args or {}

    def run(
        self,
        pipeline: Pipeline,
        catalog: DataCatalog,
        hook_manager: Optional[Union[PluginManager, _NullPluginManager]] = None,
        session_id: Optional[str] = None,
    ) -> Any:
        """Prepare Catalog and run the kedro boot app.

        Args:
            pipeline: The ``Pipeline`` to use by the kedro boot app.
            catalog: The ``DataCatalog`` from which to fetch data.
            hook_manager: The ``PluginManager`` to activate hooks.
            session_id: The id of the session.

        """
        # if not isinstance(pipeline, AppPipeline):
        #     LOGGER.warning(
        #         "No AppPipeline was given. We gonna create a '__default__' one from the given pipeline"
        #     )
        #     pipeline = app_pipeline(pipeline, name=DEFAULT_PIPELINE_VIEW_NAME)

        hook_manager = hook_manager or _NullPluginManager()
        catalog = catalog.shallow_copy()

        # Check which datasets used in the pipeline are in the catalog or match
        # a pattern in the catalog
        registered_ds = [ds for ds in pipeline.data_sets() if ds in catalog]

        # Check if there are any input datasets that aren't in the catalog and
        # don't match a pattern in the catalog.
        unsatisfied = pipeline.inputs() - set(registered_ds)

        if unsatisfied:
            raise ValueError(
                f"Pipeline input(s) {unsatisfied} not found in the DataCatalog"
            )

        # Check if there's any output datasets that aren't in the catalog and don't match a pattern
        # in the catalog.
        unregistered_ds = pipeline.data_sets() - set(registered_ds)

        # Create a default dataset for unregistered datasets
        for ds_name in unregistered_ds:
            catalog.add(ds_name, self.create_default_data_set(ds_name))

        if self._is_async:
            self._logger.info(
                "Asynchronous mode is enabled for loading and saving data"
            )

        app_return = self._run(
            pipeline,
            catalog,
            hook_manager,
            session_id,
            self._app_run_args,
            self._config_loader,
        )
        self._logger.info(f"{self._app.__class__.__name__} execution completed.")
        return app_return

    def _run(self, *args) -> Any:
        """The abstract interface for running the app. assuming that the
        inputs have already been checked and normalized by run(),

        Returns:
            Any: Any object returned at the end of execution of the app
        """
        return self._app.run(*args)

    def create_default_data_set(self, ds_name: str):
        return MemoryDataSet()
