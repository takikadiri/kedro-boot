import importlib_metadata
import logging
from typing import Union, Any
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def _safe_load_entry_point(entry_point):
    try:
        return entry_point.load()
    except Exception as exc:  # noqa: broad-except
        LOGGER.warning(
            "Failed to load %s commands from %s. Full exception: %s",
            entry_point.module,
            entry_point,
            exc,
        )
        return


def get_entry_points_commands(entry_point_key):
    entry_point_commands = []
    entry_points = importlib_metadata.entry_points().select(group=entry_point_key)
    for entry_point in entry_points:
        loaded_entry_point = _safe_load_entry_point(entry_point)
        if loaded_entry_point:
            entry_point_commands.append(loaded_entry_point)

    return entry_point_commands


def _is_project(project_path: Union[str, Path]) -> bool:
    try:
        # for retrocompatiblity with kedro >=0.19.0,<0.19.3
        from kedro.framework.startup import _is_project as _ip
    except ImportError:
        from kedro.utils import _is_project as _ip

    return _ip(project_path)


def _find_kedro_project(current_dir: Path) -> Any:
    try:
        # for retrocompatiblity with kedro >=0.19.0,<0.19.3
        from kedro.framework.startup import _find_kedro_project as _fkp
    except ImportError:
        from kedro.utils import _find_kedro_project as _fkp

    return _fkp(current_dir)
