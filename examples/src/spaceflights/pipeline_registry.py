"""Project pipelines."""
from typing import Dict

from kedro.pipeline import Pipeline
from kedro.pipeline.modular_pipeline import pipeline
# from kedro_boot.pipeline import app_pipeline

from .pipelines.data_processing import (
    create_pipeline as create_data_processing_pipeline,
)
from .pipelines.data_science import create_pipeline as create_data_science_pipeline
from .pipelines.monte_carlo import create_pipeline as create_monte_carlo_pipeline


def register_pipelines() -> Dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """
    # get pipelines
    data_processing_pipeline = create_data_processing_pipeline()
    data_science_pipeline = create_data_science_pipeline()
    monte_carlo_pipeline = create_monte_carlo_pipeline()

    ## Spaceflights App #####################
    # get ml operations nodes
    features_nodes = data_science_pipeline.only_nodes("select_features")
    model_input_nodes = data_science_pipeline.only_nodes(
        "select_features", "select_labels"
    )
    model_training_nodes = data_science_pipeline.only_nodes("split_data", "train_model")
    prediction_nodes = data_science_pipeline.only_nodes("predict")
    evaluation_nodes = data_science_pipeline.only_nodes("evaluate_model")

    # Build ml pipelines
    training_pipeline = pipeline(
        [
            model_input_nodes,
            model_training_nodes,
            pipeline(prediction_nodes, inputs={"features": "X_test"}),
            pipeline(evaluation_nodes, inputs={"labels": "y_test"}),
        ],
        inputs="features_store",
        outputs={"regression_score": None},
        namespace="training",
    )

    inference_pipeline = pipeline(
        [features_nodes, prediction_nodes],
        inputs={"regressor": "training.regressor"},
        parameters="model_options",
        namespace="inference",
    )

    evaluation_pipeline = pipeline(
        [model_input_nodes, prediction_nodes, evaluation_nodes],
        inputs={"features_store": "features_store", "regressor": "training.regressor"},
        parameters="model_options",
        namespace="evaluation",
    )

    # Concatenate all data science pipelines
    all_data_science_pipelines = (
        training_pipeline + inference_pipeline + evaluation_pipeline
    )

    ######################################
    ## Monte Carlo App : Estimating Pi #####################
    simulate_distance_pipeline = pipeline(
        monte_carlo_pipeline.only_nodes("simulate_distance"),
        namespace="simulate_distance",
    )
    estimate_pi_pipeline = pipeline(
        monte_carlo_pipeline.only_nodes("estimate_pi"),
        namespace="estimate_pi",
        parameters={"radius": "simulate_distance.radius"},
    )
    monte_carlo_pipelines = simulate_distance_pipeline + estimate_pi_pipeline

    return {
        "__default__": inference_pipeline + evaluation_pipeline,
        "data_processing": data_processing_pipeline,
        "training": training_pipeline,
        "data_science": all_data_science_pipelines,
        "monte_carlo": monte_carlo_pipelines,
    }
