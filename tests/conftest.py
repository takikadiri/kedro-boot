import pytest
from kedro.pipeline.modular_pipeline import pipeline
from kedro.pipeline import Pipeline, node


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


# @pytest.fixture
# def mock_catalog() -> DataCatalog:
#     dataset_a = MemoryDataSet(1)
#     dataset_b = MemoryDataSet(2)
#     dataset_c = MemoryDataSet(3)
#     dataset_d = MemoryDataSet()
#     dataset_e = CSVDataSet("test_data_${oc.select:date_param}.csv")
#     catalog = DataCatalog(
#         {"A": dataset_a, "B": dataset_b, "C": dataset_c, "D": dataset_d}
#     )
#     return catalog


# @pytest.fixture
# def mock_app_catalog(mock_catalog):
#     return AppCatalog(mock_catalog)
