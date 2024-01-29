from kedro.pipeline import Pipeline, node, pipeline

from .nodes import create_features_store, preprocess_companies, preprocess_shuttles


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=preprocess_companies,
                inputs="companies",
                outputs="preprocessed_companies",
                name="preprocess_companies",
            ),
            node(
                func=preprocess_shuttles,
                inputs=["shuttles"],
                outputs="preprocessed_shuttles",
                name="preprocess_shuttles",
            ),
            node(
                func=create_features_store,
                inputs=["preprocessed_shuttles", "preprocessed_companies", "reviews"],
                outputs="features_store",
                name="create_features_store",
            ),
        ]
    )  # type: ignore
