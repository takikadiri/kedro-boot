import logging
from typing import Dict, Tuple

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split


def select_features(features_stores: pd.DataFrame, parameters: Dict) -> Tuple:
    """Select features from features_store.

    Args:
        features_store: Data containing features and target.
        parameters: Parameters defined in parameters/data_science.yml.
    Returns:
        Features.
    """
    features = features_stores[parameters["features"]]
    return features


def select_labels(features_stores) -> Tuple:
    """Select labels from features_store.

    Args:
        features_store: Data containing features and target.
        parameters: Parameters defined in parameters/data_science.yml.
    Returns:
        Labels.
    """
    labels = features_stores["price"]
    return labels


def split_data(features: pd.DataFrame, labels: pd.DataFrame, parameters: Dict) -> Tuple:
    """Splits data into features and targets training and test sets.

    Args:
        data: Data containing features and target.
        parameters: Parameters defined in parameters/data_science.yml.
    Returns:
        Split data.
    """

    X_train, X_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=parameters["test_size"],
        random_state=parameters["random_state"],
    )
    return X_train, X_test, y_train, y_test


def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> LinearRegression:
    """Trains the linear regression model.

    Args:
        X_train: Training data of independent features.
        y_train: Training data for price.

    Returns:
        Trained model.
    """
    regressor = LinearRegression()
    regressor.fit(X_train, y_train)
    return regressor


def predict(regressor: LinearRegression, features: pd.DataFrame):
    """Predict price shutlles using regressor model.

    Args:
        regressor: Trained model.
        features: independent features.
    """
    predictions = regressor.predict(features)
    return predictions.tolist()


def evaluate_model(predictions: pd.Series, labels: pd.Series, r2_multioutput: str):
    """Calculates and logs the coefficient of determination.

    Args:
        predictions: predictions on a set of features.
        labels: Testing data for price (label).
    """
    score = r2_score(labels, predictions, multioutput=r2_multioutput)
    logger = logging.getLogger(__name__)
    logger.info("Model has a coefficient R^2 of %.3f on test data.", score)
    return {"regression_score": score}
