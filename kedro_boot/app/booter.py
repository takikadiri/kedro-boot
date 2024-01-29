"""A factory funtion for creating kedro boot session within standalone apps"""

from pathlib import Path
from typing import List, Optional, Union
from kedro.framework.startup import bootstrap_project
from kedro.framework.project import configure_project

from kedro_boot.framework.session import KedroBootSession

from kedro_boot.framework.compiler.specs import CompilationSpec
from kedro_boot.framework.cli.factory import create_kedro_booter

from kedro_boot.app import BooterApp


def boot_project(
    project_path: Optional[Union[Path, str, None]] = None,
    kedro_args: dict = None,
    compilation_specs: List[CompilationSpec] = None,
) -> KedroBootSession:
    project_path = project_path or Path(project_path or Path.cwd()).resolve()

    bootstrap_project(project_path)

    kedro_session_create_args = dict(project_path=project_path)

    return boot_session(
        kedro_session_create_args=kedro_session_create_args,
        kedro_args=kedro_args,
        compilation_specs=compilation_specs,
    )


def boot_package(
    package_name: Optional[str],
    kedro_args: dict = None,
    compilation_specs: List[CompilationSpec] = None,
) -> KedroBootSession:
    configure_project(package_name)

    return boot_session(kedro_args=kedro_args, compilation_specs=compilation_specs)


def boot_session(
    kedro_session_create_args: dict = None,
    kedro_args: dict = None,
    compilation_specs: List[CompilationSpec] = None,
):
    kedro_session_create_args = kedro_session_create_args or {}
    kedro_session_create_args["save_on_close"] = False

    kedro_args = kedro_args or {}

    kedro_booter = create_kedro_booter(
        kedro_session_create_args=kedro_session_create_args,
        app_class=BooterApp,
        app_args={"compilation_specs": compilation_specs},
    )

    return kedro_booter(**kedro_args)
