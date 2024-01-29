# from .utils import get_routes_data_models
import logging

from kedro_boot.app.fastapi.session import kedro_fastapi_session

LOGGER = logging.getLogger(__name__)


def post_worker_init(worker):
    fastapi_app = worker.app.wsgi()
    fastapi_app.dependency_overrides[kedro_fastapi_session].compile(fastapi_app)
    LOGGER.info(
        "Kedro Boot Catalog compilation is completed. Ready to serve your app !"
    )
