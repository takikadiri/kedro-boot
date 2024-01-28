"""``AbstractKedroBootApp`` is the base class for all kedro boot app implementations.
"""
from abc import ABC, abstractmethod
from typing import Any, List

from kedro.config import OmegaConfigLoader
from kedro.io import DataCatalog
from pluggy import PluginManager

from kedro.pipeline.pipeline import Pipeline
from kedro_boot.framework.session import KedroBootSession
from kedro_boot.framework.compiler.specs import CompilationSpec


class AbstractKedroBootApp(ABC):
    """``AbstractKedroBootApp`` is the base class for all kedro boot app implementations"""

    LAZY_COMPILE = False

    def __init__(self, compilation_specs: List[CompilationSpec] = None) -> None:
        self._compilation_specs = compilation_specs

    def run(
        self,
        pipeline: Pipeline,
        catalog: DataCatalog,
        hook_manager: PluginManager,
        session_id: str,
        app_runtime_params: dict,
        config_loader: OmegaConfigLoader,
    ) -> Any:
        """Create a ``KedroBootSession`` then run the kedro boot app

        Args:
            pipeline: The ``AppPipeline`` containing the multiple views to the base pipeline.
            catalog: The base ``DataCatalog`` from which to fetch data.
            hook_manager: The ``PluginManager`` to activate hooks.
            session_id: The id of the kedro session.
            runtime_app_params (dict): params given by an App specific CLI
            config_loader (OmegaConfigLoader): kedro ``OmegaConfigLoader`` object

        Returns:
            Any: the return value of the kedro boot app run method
        """

        config_loader.update({"application": ["application*/"]})

        session = KedroBootSession(
            pipeline=pipeline,
            catalog=catalog,
            hook_manager=hook_manager,
            session_id=session_id,
            app_runtime_params=app_runtime_params,
            config_loader=config_loader,
        )

        if not self.LAZY_COMPILE:
            session.compile(compilation_specs=self._compilation_specs)

        return self._run(session)

    @abstractmethod
    def _run(self, session: KedroBootSession) -> Any:
        """The abstract interface for running kedro boot apps, assuming that the
        ``KedrobootSession`` have already be created by run().

        Args:
            session (KedroBootSession): A user facing interface that expose kedro's resource to the kedro boot apps
        """
        pass


class DummyApp(AbstractKedroBootApp):
    """A Dummy app that do a simple run.
    Using this app is equivalent to using kedro without kedro boot.

    Args:
        AbstractKedroBootApp (_type_): _description_
    """

    def _run(self, session: KedroBootSession) -> Any:
        return session.run()


class CompileApp(AbstractKedroBootApp):
    """An App used to perform Dry Run.

    Args:
        AbstractKedroBootApp (_type_): _description_
    """

    def _run(self, session: KedroBootSession) -> Any:
        pass
