import pytest
from kedro_boot.catalog import AppCatalog
from kedro.pipeline.modular_pipeline import pipeline
from kedro.pipeline import Pipeline, node
from kedro.io import MemoryDataSet, DataCatalog
from kedro.extras.datasets.pandas import CSVDataSet


@pytest.fixture
def mock_pipeline() -> Pipeline:
    def identity(x, y):
        return x

    def square(x):
        return x**2

    def cube(x):
        return x**3

    nodes = [
        node(identity, ["A", "B"], "C", name="identity"),
        node(square, "C", "D"),
        node(cube, "D", None),
    ]

    return pipeline(nodes)


@pytest.fixture
def mock_catalog() -> DataCatalog:
    dataset_a = MemoryDataSet(1)
    dataset_b = MemoryDataSet(2)
    dataset_c = MemoryDataSet(3)
    dataset_d = CSVDataSet("data/01_raw/test_data_[[ date_param ]].csv")
    catalog = DataCatalog(
        {"A": dataset_a, "B": dataset_b, "C": dataset_c, "D": dataset_d}
    )
    return catalog


@pytest.fixture
def mock_app_catalog(mock_catalog):
    return AppCatalog(mock_catalog)
