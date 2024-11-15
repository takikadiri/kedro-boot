"""Kedro Boot is a Kedro plugin that streamlines the integration between Kedro projects and external applications."""

__version__ = "0.2.3"

import logging

kedro_boot_logger = logging.getLogger(__name__)
kedro_boot_logger.setLevel(logging.INFO)
