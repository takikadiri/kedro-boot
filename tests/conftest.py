import pytest
from kedro.pipeline.modular_pipeline import pipeline
from kedro.pipeline import Pipeline, node
from cookiecutter.main import cookiecutter
from kedro import __version__ as kedro_version
from kedro.framework.startup import _add_src_to_path


@pytest.fixture
def mock_pipeline() -> Pipeline:
    def identity(x, y):
        return x * y

    def square(x):
        return x**2

    def cube(x):
        return x**3, {"results": x**3}

    nodes = [
        node(identity, ["A", "params:B"], "C", name="identity"),
        node(square, "C", "D"),
        node(cube, "D", ["E", "F"]),
    ]

    return pipeline(nodes)


_FAKE_PROJECT_NAME = "fake_project"


@pytest.fixture
def kedro_project(tmp_path):
    # TODO : this is also an integration test since this depends from the kedro version
    config = {
        # "output_dir": tmp_path,
        "project_name": _FAKE_PROJECT_NAME,
        "repo_name": _FAKE_PROJECT_NAME,
        "python_package": _FAKE_PROJECT_NAME,
        "kedro_version": kedro_version,
        "tools": "['None']",
        "example_pipeline": "True",
    }

    cookiecutter(
        "https://github.com/kedro-org/kedro-starters.git",
        directory="spaceflights-pandas",
        output_dir=tmp_path,  # config["output_dir"],
        no_input=True,
        extra_context=config,
        accept_hooks=True,
    )

    _add_src_to_path(
        tmp_path / _FAKE_PROJECT_NAME / "src", tmp_path / _FAKE_PROJECT_NAME
    )

    return tmp_path / _FAKE_PROJECT_NAME
