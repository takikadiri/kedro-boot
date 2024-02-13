import logging
import platform

from kedro.config import MissingConfigException
from kedro.utils import load_obj

from kedro_boot.app import AbstractKedroBootApp
from kedro_boot.framework.session import KedroBootSession

LOGGER = logging.getLogger(__name__)


class FastApiApp(AbstractKedroBootApp):
    LAZY_COMPILE = True

    def load_app(self, app: str):
        app_class = app or "kedro_boot.app.fastapi.starter_apps.runner.app"

        return load_obj(app_class)

    def get_configs(self, server_cli_options: dict, server_file_options: dict):
        server_options = {"host": "127.0.0.1", "port": 8000, "workers": 1}

        server_cli_options = {
            k: v for k, v in server_cli_options.items() if v is not None
        }

        server_options.update(server_file_options)
        server_options.update(server_cli_options)

        return server_options

    def _run(self, kedro_boot_session: KedroBootSession):
        try:
            import uvicorn
            from pyctuator.pyctuator import Pyctuator
            from kedro_boot.app.fastapi.session import (
                KedroFastApiSession,
                kedro_fastapi_session,
            )
        except (ImportError, ModuleNotFoundError) as e:
            raise FastApiAppException(
                f"{e.msg}. If you're using the Kedro FastAPI Server, you should consider installing fastapi extra dependencies 'pip install kedro-boot[fastapi]'"
            )

        kedro_boot_session.config_loader.config_patterns.update(
            {"fastapi": ["fastapi*/"]}
        )

        try:
            server_file_options = kedro_boot_session.config_loader["fastapi"].get(
                "server", {}
            )
        except MissingConfigException:
            LOGGER.warning(
                "No 'fastapi.yml' nor 'fastapi.yaml' config file found in environment. Default configuration will be used"
            )
            server_file_options = {}

        configs = self.get_configs(
            server_cli_options=kedro_boot_session.app_runtime_params,
            server_file_options=server_file_options,
        )
        app = self.load_app(configs.pop("app", None))

        Pyctuator(
            app,
            "Kedro FastAPI Pyctuator",
            app_url=None,
            pyctuator_endpoint_url="/actuator",
            registration_url=None,
        )

        if platform.system().lower() == "windows":
            LOGGER.info(
                "You are using Windows OS. uvicorn will be used as web server. Multiple workers are not supported with this setup. Please consider using Linux or Mac OS as it leverage Gunicorn capabilities."
            )

            if configs.get("workers"):
                LOGGER.warning(
                    "kedro-boot fastapi does not support multiple workers config in Windows OS, we'll use just one uvicorn worker. Please consider using Linux or Mac as it leverage Gunicorn capabilities"
                )
                configs.pop("workers")

            configs.update(configs.get("extra_uvicorn", {}))
            if configs.get("extra_uvicorn"):
                configs.pop("extra_uvicorn")

            kedro_fastapi_materialized_session = KedroFastApiSession(kedro_boot_session)
            kedro_fastapi_materialized_session.compile(app)
            app.dependency_overrides[
                kedro_fastapi_session
            ] = kedro_fastapi_materialized_session

            uvicorn.run(app=app, **configs)

        else:
            from .gunicorn import GunicornApp

            LOGGER.info("You are using Linux OS. Gunicorn will be used as web server")

            configs["bind"] = f"{configs.get('host')}:{configs.get('port')}"
            configs["worker_class"] = "uvicorn.workers.UvicornH11Worker"
            configs.update(configs.get("extra_gunicorn", {}))

            if configs.get("extra_gunicorn"):
                configs.pop("extra_gunicorn")
            if configs.get("host"):
                configs.pop("host")
            if configs.get("port"):
                configs.pop("port")

            app.dependency_overrides[kedro_fastapi_session] = KedroFastApiSession(
                kedro_boot_session
            )

            GunicornApp(app, configs).run()


class FastApiAppException(Exception):
    """Error raised in FastApiApp operations"""
