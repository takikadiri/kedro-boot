import importlib_metadata
import logging

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
