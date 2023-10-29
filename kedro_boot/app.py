"""``AbstractKedroBootApp`` is the base class for all kedro boot app implementations.
"""
from abc import ABC, abstractmethod
from typing import Any

from kedro.config import ConfigLoader
from kedro.io import DataCatalog
from pluggy import PluginManager

from kedro_boot.pipeline import AppPipeline
from kedro_boot.session import KedroBootSession


class AbstractKedroBootApp(ABC):
    """``AbstractKedroBootApp`` is the base class for all kedro boot app implementations"""

    def run(
        self,
        pipeline: AppPipeline,
        catalog: DataCatalog,
        hook_manager: PluginManager,
        session_id: str,
        config_loader: ConfigLoader,
        lazy_compile: bool,
    ) -> Any:
        """Create a ``KedroBootSession`` then run the kedro boot app

        Args:
            pipeline: The ``AppPipeline`` containing the multiple views to the base pipeline.
            catalog: The base ``DataCatalog`` from which to fetch data.
            hook_manager: The ``PluginManager`` to activate hooks.
            session_id: The id of the kedro session.

        Returns:
            Any: the return value of the kedro boot app run method
        """

        session = KedroBootSession(
            pipeline=pipeline,
            catalog=catalog,
            hook_manager=hook_manager,
            session_id=session_id,
            config_loader=config_loader,
        )

        if not lazy_compile:
            session.compile_catalog()

        return self._run(session)

    @abstractmethod
    def _run(self, session: KedroBootSession) -> Any:
        """The abstract interface for running kedro boot apps, assuming that the
        ``KedrobootSession`` have already be created by run().

        Args:
            session (KedroBootSession): is the object that is responsible for managing the kedro boot app lifecycle
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


class DryRunApp(AbstractKedroBootApp):
    """An App used to perform Dry Run.

    Args:
        AbstractKedroBootApp (_type_): _description_
    """

    def _run(self, session: KedroBootSession) -> Any:
        pass


class BridgeApp(AbstractKedroBootApp):
    """An App used by the booter to pass the instantiated kedro boot session.

    Args:
        AbstractKedroBootApp (_type_): _description_
    """

    def _run(self, session: KedroBootSession) -> KedroBootSession:
        return session
