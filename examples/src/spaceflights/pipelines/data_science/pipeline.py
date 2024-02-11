from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    evaluate_model,
    predict,
    select_features,
    select_labels,
    split_data,
    train_model,
)


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=select_features,
                inputs=["features_store", "params:model_options"],
                outputs="features",
                name="select_features",
            ),
            node(
                func=select_labels,
                inputs=["features_store"],
                outputs="labels",
                name="select_labels",
            ),
            node(
                func=split_data,
                inputs=["features", "labels", "params:model_options"],
                outputs=["X_train", "X_test", "y_train", "y_test"],
                name="split_data",
            ),
            node(
                func=train_model,
                inputs=["X_train", "y_train"],
                outputs="regressor",
                name="train_model",
            ),
            node(
                func=predict,
                inputs=["regressor", "features"],
                outputs="predictions",
                name="predict",
            ),
            node(
                func=evaluate_model,
                inputs=["predictions", "labels", "params:r2_multioutput"],
                outputs="regression_score",
                name="evaluate_model",
            ),
        ]
    )  # type: ignore
