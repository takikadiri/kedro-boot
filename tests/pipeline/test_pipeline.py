from kedro.pipeline import Pipeline, node
from kedro_boot.pipeline.pipeline import AppPipeline, PipelineView, AppPipelineError
import pytest


def test_app_pipeline():
    def identity(x):
        return x

    def square(x):
        return x**2

    def cube(x):
        return x**3

    nodes = [
        node(identity, "A", "B"),
        node(square, "B", "C"),
        node(cube, "C", "D"),
    ]

    view1 = PipelineView(name="view1", inputs=["A"], outputs=["D"])
    view2 = PipelineView(name="view2", inputs=["A"], outputs=["C"])
    view3 = PipelineView(name="view3", inputs=["A"], outputs=["B", "C", "D"])

    pipeline = AppPipeline(nodes=nodes, views=[view1, view2, view3])

    assert isinstance(pipeline, Pipeline)
    assert isinstance(pipeline, AppPipeline)
    assert len(pipeline.views) == 3

    assert pipeline.get_view("view1").inputs == ["A"]
    assert pipeline.get_view("view1").outputs == ["D"]

    assert pipeline.get_view("view2").inputs == ["A"]
    assert pipeline.get_view("view2").outputs == ["C"]

    assert pipeline.get_view("view3").inputs == ["A"]
    assert pipeline.get_view("view3").outputs == ["B", "C", "D"]

    with pytest.raises(AppPipelineError):
        pipeline.get_view("view4")

    pipeline2 = AppPipeline(nodes=nodes[:2], views=[view1, view2]) + AppPipeline(
        nodes=nodes[2:], views=[view3]
    )

    assert pipeline2.views == [view1, view2, view3]
    assert pipeline2.nodes == nodes

    pipeline3 = AppPipeline(nodes=nodes, views=[view1, view2])

    with pytest.raises(ValueError):
        pipeline + pipeline3

    with pytest.raises(NotImplementedError):
        pipeline - pipeline2

    with pytest.raises(NotImplementedError):
        pipeline & pipeline2

    with pytest.raises(NotImplementedError):
        pipeline | pipeline2
