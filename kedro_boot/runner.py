"""``KedroBootRunner`` is the kedro runner that instantiate and run the kedro boot app."""
import logging
from typing import Any, Optional, Union

from kedro.config import ConfigLoader
from kedro.framework.hooks.manager import _NullPluginManager
from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline
from kedro.runner import AbstractRunner
from kedro.utils import load_obj
from pluggy import PluginManager

from kedro_boot.app import AbstractKedroBootApp
from kedro_boot.pipeline import DEFAULT_PIPELINE_VIEW_NAME, AppPipeline, app_pipeline

LOGGER = logging.getLogger(__name__)


class KedroBootRunner(AbstractRunner):
    """``KedroBootRunner`` is the kedro runner that instantiate and run the kedro boot app."""

    def __init__(
        self,
        config_loader: ConfigLoader,
        app_class: str,
        app_args: Optional[dict] = None,
        lazy_compile: bool = False,
        **runner_args,
    ):
        """Instantiate the kedro boot runner

        Args:
            config_loader (ConfigLoader): kedro config loader
            app_class (str): Path to the kedro boot app object. ex: kedro_boot.app.KedroBootApp
            app_args (dict): Args used for initializing kedro boot app object. Defaults to None.
        """

        super().__init__(**runner_args)

        self.config_loader = config_loader

        app_args = app_args or {}
        obj_class = load_obj(app_class)
        if not issubclass(obj_class, AbstractKedroBootApp):
            raise TypeError(
                f"app_class must be a subclass of AbstractKedroBootApp, got {obj_class.__name__}"
            )
        self.app_obj = obj_class(**app_args) if app_args else obj_class()

        self.lazy_compile = lazy_compile

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
        if not isinstance(pipeline, AppPipeline):
            LOGGER.warning(
                "No AppPipeline was given. We gonna create a '__default__' one from the given pipeline"
            )
            pipeline = app_pipeline(pipeline, name=DEFAULT_PIPELINE_VIEW_NAME)

        hook_manager = hook_manager or _NullPluginManager()
        catalog = catalog.shallow_copy()

        unsatisfied = pipeline.inputs() - set(catalog.list())
        if unsatisfied:
            raise ValueError(
                f"Pipeline input(s) {unsatisfied} not found in the DataCatalog"
            )

        unregistered_ds = pipeline.data_sets() - set(catalog.list())
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
            self.config_loader,
            self.lazy_compile,
        )
        self._logger.info(f"{self.app_obj.__class__.__name__} execution completed.")
        return app_return

    def _run(self, *args) -> Any:
        """The abstract interface for running the app. assuming that the
        inputs have already been checked and normalized by run(),

        Returns:
            Any: Any object returned at the end of execution of the app
        """
        return self.app_obj.run(*args)

    def create_default_data_set(self, ds_name: str):
        return MemoryDataSet()
