from pathlib import Path
from kedro_boot.app.booter import boot_project


def test_boot_project(
    kedro_project: Path,
):
    project_session = boot_project(project_path=kedro_project)
    assert project_session

    # # TODO: for package_project the dataset filapath of the example are relative. This raise error when loading them
    # package_session = boot_package(package_name="fake_project", kedro_args={"conf_source": kedro_project / "conf"})
    # assert package_session
