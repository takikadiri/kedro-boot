"""``KedroBootAdapter`` transform a Kedro Session Run to a booting process."""

from concurrent.futures import Executor
import logging
from time import perf_counter
from typing import Any, Optional, Union

from kedro.config import OmegaConfigLoader
from kedro.framework.hooks.manager import _NullPluginManager
from kedro.pipeline import Pipeline
from kedro.io import CatalogProtocol, SharedMemoryCatalogProtocol
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
        super().__init__()

        self._app = app
        self._config_loader = config_loader
        self._app_runtime_params = app_runtime_params or {}

    def _get_executor(self, max_workers: int) -> Executor:
        """Abstract method to provide the correct executor (e.g., ThreadPoolExecutor or ProcessPoolExecutor)."""
        pass

    def run(
        self,
        pipeline: Pipeline,
        catalog: CatalogProtocol | SharedMemoryCatalogProtocol,
        hook_manager: Optional[Union[PluginManager, _NullPluginManager]] = None,
        run_id: Optional[str] = None,
        only_missing_outputs: bool = False,
    ) -> Any:
        """Prepare Catalog and run the kedro boot app.

        Args:
            pipeline: The ``Pipeline`` to use by the kedro boot app.
            catalog: The ``DataCatalog`` from which to fetch data.
            hook_manager: The ``PluginManager`` to activate hooks.
            run_id: The id of the run.

        """

        # Apply missing outputs filtering if requested
        if only_missing_outputs:
            pipeline = self._filter_pipeline_for_missing_outputs(pipeline, catalog)

        # Check which datasets used in the pipeline are in the catalog or match
        # a pattern in the catalog, not including extra dataset patterns
        # Run a warm-up to materialize all datasets in the catalog before run
        warmed_up_ds = []
        for ds in pipeline.datasets():
            if ds in catalog:
                warmed_up_ds.append(ds)
            _ = catalog.get(ds, fallback_to_runtime_pattern=True)

        # Check if there are any input datasets that aren't in the catalog and
        # don't match a pattern in the catalog.
        unsatisfied = pipeline.inputs() - set(warmed_up_ds)

        if unsatisfied:
            raise ValueError(
                f"Pipeline input(s) {unsatisfied} not found in the {catalog.__class__.__name__}"
            )

        hook_or_null_manager = hook_manager or _NullPluginManager()

        start_time = perf_counter()
        app_return = self._run(
            pipeline,
            catalog,
            hook_or_null_manager,
            run_id,
            self._app_runtime_params,
            self._config_loader,
        )
        end_time = perf_counter()
        run_duration = end_time - start_time

        self._logger.info(
            f"{self._app.__class__.__name__} execution completed in {run_duration:.1f} sec.."
        )
        return app_return

    def _run(self, *args) -> Any:
        """The abstract interface for running the app. assuming that the
        inputs have already been checked and normalized by run(),

        Returns:
            Any: Any object returned at the end of execution of the app
        """
        return self._app.run(*args)
