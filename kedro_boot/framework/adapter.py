"""``KedroBootAdapter`` transform a Kedro Session Run to a booting process."""
import logging
from typing import Any, Optional, Union

from kedro.config import OmegaConfigLoader
from kedro.framework.hooks.manager import _NullPluginManager
from kedro.pipeline import Pipeline
from kedro.io import DataCatalog
from kedro.runner import AbstractRunner
from pluggy import PluginManager

from kedro_boot.app import AbstractKedroBootApp

LOGGER = logging.getLogger(__name__)


class KedroBootAdapter(AbstractRunner):
    """``KedroBootRunner`` transform a Kedro Session Run to a booting process."""

    def __init__(
        self,
        app: AbstractKedroBootApp,
        config_loader: OmegaConfigLoader,
        app_runtime_params: Optional[dict] = None,
    ):
        """Instantiate the kedro boot adapter

        Args:
            app (AbstractKedroBootApp): Kedro Boot App object
            config_loader (OmegaConfigLoader): kedro config loader
            app_run_args (dict): App runtime args given by App CLI
        """

        self._extra_dataset_patterns = {"{default}": {"type": "MemoryDataset"}}
        super().__init__(extra_dataset_patterns=self._extra_dataset_patterns)

        self._app = app
        self._config_loader = config_loader
        self._app_runtime_params = app_runtime_params or {}

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
        hook_or_null_manager = hook_manager or _NullPluginManager()
        catalog = catalog.shallow_copy()

        # Check which datasets used in the pipeline are in the catalog or match
        # a pattern in the catalog
        registered_ds = [ds for ds in pipeline.datasets() if ds in catalog]

        # Check if there are any input datasets that aren't in the catalog and
        # don't match a pattern in the catalog.
        unsatisfied = pipeline.inputs() - set(registered_ds)

        if unsatisfied:
            raise ValueError(
                f"Pipeline input(s) {unsatisfied} not found in the DataCatalog"
            )

        # Register the default dataset pattern with the catalog
        catalog = catalog.shallow_copy(
            extra_dataset_patterns=self._extra_dataset_patterns
        )

        app_return = self._run(
            pipeline,
            catalog,
            hook_or_null_manager,
            session_id,
            self._app_runtime_params,
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
