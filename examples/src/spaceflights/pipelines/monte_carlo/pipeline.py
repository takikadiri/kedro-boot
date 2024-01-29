"""
This is a boilerplate pipeline 'monte_carlo'
generated using Kedro 0.18.14
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import estimate_pi, simulate_distance


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=simulate_distance,
                inputs="params:radius",
                outputs="distance",
                name="simulate_distance",
            ),
            node(
                func=estimate_pi,
                inputs=["distances", "params:radius", "params:num_samples"],
                outputs="pi",
                name="estimate_pi",
            ),
        ]
    )  # type: ignore
