"""A factory funtion for creating kedro boot session within external apps"""

import copy
from pathlib import Path
from typing import Optional

from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

from kedro_boot.runner import KedroBootRunner
from kedro_boot.session import KedroBootSession


def boot_session(
    project_path: Optional[Path] = None,
    pipeline_name: Optional[str] = None,
    env: Optional[str] = None,
    extra_params: Optional[dict] = None,
    lazy_compile: Optional[bool] = False,
    **session_run_kwargs,
) -> KedroBootSession:
    """Create ``KedroBootSession`` from kedro project. ``KedroBootSession`` is used by the kedro boot app to perform multiple low latency runs of the pipeline with the possibility of injecting data at each iteration.

    Args:
        project_path (Path): Kedro project path. Defaults to the current working directory.
        pipeline_name (str): Name of the project running pipeline. Default to __Default__
        env (str): Kedro project env. Defaults to base.
        extra_params (dict): Inject extra params to kedro project. Defaults to None.
        lazy_compile (bool): AppCatalog compilation mode. By default kedro boot autmatically compile before starting the app. If lazy mode activated, the compilation processed need to be triggered by the app or lazily at first iteration run. Defaults to False.
        session_run_kwargs (dict): KedroSession.run kwargs. Defaults to None.

    Returns:
        KedroBootSession: _description_
    """

    # TODO: Add support for packaged kedro projects

    boot_project_path = Path(project_path or Path.cwd()).resolve()

    project_metadata = bootstrap_project(boot_project_path)
    kedro_session = KedroSession.create(
        project_metadata.package_name,
        project_path=boot_project_path,
        env=env,
        extra_params=extra_params,
    )

    boot_session_args = copy.deepcopy(session_run_kwargs)
    if "pipeline_name" in boot_session_args:
        boot_session_args.pop("pipeline_name")
    if "runner" in boot_session_args:
        boot_session_args.pop("runner")

    return kedro_session.run(
        pipeline_name=pipeline_name,
        runner=KedroBootRunner(
            config_loader=kedro_session._get_config_loader(),
            app_class="kedro_boot.app.BridgeApp",
            lazy_compile=lazy_compile,
        ),
        **boot_session_args,
    )  # type: ignore
