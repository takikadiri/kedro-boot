from kedro_boot.pipeline.factory import (
    app_pipeline,
    AppPipelineFactoryError,
    create_dummy_pipeline,
)
from kedro.pipeline import Pipeline, node
import pytest

from kedro_boot.pipeline.pipeline import AppPipeline


@pytest.mark.parametrize(
    "pipeline_attributes, expected_pipeline_attributes",
    [
        (
            {
                "inputs": ["input1"],
                "outputs": ["output2"],
                "parameters": ["param1"],
                "artifacts": ["art1"],
                "infer_artifacts": True,
            },
            {
                "inputs": ["input1"],
                "outputs": ["output2"],
                "parameters": ["param1"],
                "artifacts": ["art1"],
                "infer_artifacts": False,
            },
        ),
        (
            {
                "inputs": ["input1"],
                "outputs": ["output2"],
                "parameters": ["param1"],
                "artifacts": ["art1"],
                "infer_artifacts": False,
            },
            {
                "inputs": ["input1"],
                "outputs": ["output2"],
                "parameters": ["param1"],
                "artifacts": ["art1"],
                "infer_artifacts": False,
            },
        ),
        (
            {
                "inputs": ["input1"],
                "outputs": ["output2"],
                "parameters": ["param1"],
                "artifacts": None,
                "infer_artifacts": False,
            },
            {
                "inputs": ["input1"],
                "outputs": ["output2"],
                "parameters": ["param1"],
                "artifacts": [],
                "infer_artifacts": False,
            },
        ),
        (
            {
                "inputs": {"input1"},
                "outputs": {"output2"},
                "parameters": ["param1"],
                "artifacts": None,
                "infer_artifacts": None,
            },
            {
                "inputs": ["input1"],
                "outputs": ["output2"],
                "parameters": ["param1"],
                "artifacts": [],
                "infer_artifacts": False,
            },
        ),
        (
            {
                "inputs": "input1",
                "outputs": "output2",
                "parameters": ["param1"],
                "artifacts": None,
                "infer_artifacts": True,
            },
            {
                "inputs": ["input1"],
                "outputs": ["output2"],
                "parameters": ["param1"],
                "artifacts": [],
                "infer_artifacts": True,
            },
        ),
        (
            {
                "inputs": ["input1"],
                "outputs": None,
                "parameters": None,
                "artifacts": None,
                "infer_artifacts": None,
            },
            {
                "inputs": ["input1"],
                "outputs": [],
                "parameters": [],
                "artifacts": [],
                "infer_artifacts": False,
            },
        ),
        (
            {
                "inputs": ["input1", "input2"],
                "outputs": None,
                "parameters": None,
                "artifacts": None,
                "infer_artifacts": None,
            },
            {
                "inputs": ["input1", "input2"],
                "outputs": [],
                "parameters": [],
                "artifacts": [],
                "infer_artifacts": False,
            },
        ),
    ],
)
def test_app_pipeline_with_different_arguments(
    pipeline_attributes, expected_pipeline_attributes
):
    def test_func1(a, b, c, d):  # -> Any:
        return a

    def test_func2(a):
        return a

    pipeline1 = Pipeline(
        [node(test_func1, ["input1", "input2", "art1", "params:param1"], "output1")]
    )
    pipeline2 = Pipeline([node(test_func2, "output1", "output2")])
    test_app_pipeline = app_pipeline(
        [pipeline1, pipeline2],
        name="test",
        inputs=pipeline_attributes["inputs"],
        outputs=pipeline_attributes["outputs"],
        parameters=pipeline_attributes["parameters"],
        artifacts=pipeline_attributes["artifacts"],
        infer_artifacts=pipeline_attributes["infer_artifacts"],
    )

    assert isinstance(test_app_pipeline, AppPipeline)
    assert len(test_app_pipeline.only_nodes_with_tags("test").nodes) == len(
        test_app_pipeline.nodes
    )
    assert len(test_app_pipeline.views) == 1
    assert test_app_pipeline.views[0].name == "test"
    assert set(test_app_pipeline.views[0].inputs) == set(
        expected_pipeline_attributes["inputs"]
    )
    assert set(test_app_pipeline.views[0].outputs) == set(
        expected_pipeline_attributes["outputs"]
    )
    assert set(test_app_pipeline.views[0].parameters) == set(
        expected_pipeline_attributes["parameters"]
    )
    assert set(test_app_pipeline.views[0].artifacts) == set(
        expected_pipeline_attributes["artifacts"]
    )
    assert (
        test_app_pipeline.views[0].infer_artifacts
        == expected_pipeline_attributes["infer_artifacts"]
    )


def test_app_pipeline_with_duplicate_view_names():
    pipeline1 = app_pipeline([node(lambda x: x, "input1", "output1")], name="test")
    pipeline2 = app_pipeline([node(lambda x: x, "input2", "output2")], name="test")
    with pytest.raises(ValueError):
        app_pipeline([pipeline1, pipeline2], name="test")


def test_app_pipeline_with_tag_already_used_in_pipeline():
    pipeline = Pipeline([node(lambda x: x, "input1", "output1", tags=["test"])])
    with pytest.raises(AppPipelineFactoryError):
        app_pipeline(pipeline, name="test")


def test_create_dummy_pipeline():
    pipeline = create_dummy_pipeline()
    assert isinstance(pipeline, Pipeline)
    assert len(pipeline.nodes) == 1
