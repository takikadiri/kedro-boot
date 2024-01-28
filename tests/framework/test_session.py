from typing import List
from kedro_boot.framework.session.session import KedroBootSession
import pytest
from kedro.pipeline import Pipeline
from kedro.pipeline.modular_pipeline import pipeline
from kedro.framework.hooks.manager import _NullPluginManager
from kedro.config import OmegaConfigLoader
from kedro.io import DataCatalog, MemoryDataset
from kedro_datasets.json import JSONDataset

template_filepath = "test_data_${oc.select:date_param,01_01_1960}.csv"
parametrized_test_session_scenarios = [
    (  # Test a non-namespaced pipeline
        [{"namespace": None}],
        DataCatalog(
            {
                "A": MemoryDataset(2),
                "params:B": MemoryDataset(1),
                "C": MemoryDataset(),
                "D": MemoryDataset(),
                "E": MemoryDataset(),
                "F": JSONDataset(filepath=template_filepath),
            }
        ),
        {},
        {"E": 64},
    ),
    (  # Test pipeline namespace with all attributes are namespaced
        [{"namespace": "n1"}],
        DataCatalog(
            {
                "n1.A": MemoryDataset(2),
                "params:n1.B": MemoryDataset(1),
                "n1.C": MemoryDataset(),
                "n1.D": MemoryDataset(),
                "n1.E": MemoryDataset(),
                "n1.F": JSONDataset(filepath=template_filepath),
            }
        ),
        {"namespace": "n1", "inputs": {"A": 1}, "parameters": {"B": 1}},
        {"n1.E": 1, "n1.F": {"results": 1}},
    ),
    (  # Test pipeline namespace with non-namespaced inputs
        [{"namespace": "n1", "inputs": "A"}],
        DataCatalog(
            {
                "n1.A": MemoryDataset(2),
                "params:n1.B": MemoryDataset(1),
                "n1.C": MemoryDataset(),
                "n1.D": MemoryDataset(),
                "n1.E": MemoryDataset(),
                "n1.F": JSONDataset(filepath=template_filepath),
                "A": MemoryDataset(2),
                "params:B": MemoryDataset(1),
                "C": MemoryDataset(),
                "D": MemoryDataset(),
                "E": MemoryDataset(),
                "F": JSONDataset(filepath=template_filepath),
            }
        ),
        {"namespace": "n1", "parameters": {"B": 1}},
        {"n1.E": 64, "n1.F": {"results": 64}},
    ),
    (  # Test pipeline namespace with non-namespaced inputs and outputs
        [{"namespace": "n1", "inputs": "A", "outputs": "F"}],
        DataCatalog(
            {
                "n1.A": MemoryDataset(2),
                "params:n1.B": MemoryDataset(1),
                "n1.C": MemoryDataset(),
                "n1.D": MemoryDataset(),
                "n1.E": MemoryDataset(),
                "F": JSONDataset(filepath=template_filepath),
                "A": MemoryDataset(2),
            }
        ),
        {"namespace": "n1", "parameters": {"B": 1}},
        64,
    ),
    (  # Test pipeline containing None and not-None namespaces
        [{"namespace": None}, {"namespace": "n1"}],
        DataCatalog(
            {
                "n1.A": MemoryDataset(2),
                "params:n1.B": MemoryDataset(1),
                "n1.C": MemoryDataset(),
                "n1.D": MemoryDataset(),
                "n1.E": MemoryDataset(),
                "n1.F": JSONDataset(filepath=template_filepath),
                "A": MemoryDataset(2),
                "params:B": MemoryDataset(1),
                "C": MemoryDataset(),
                "D": MemoryDataset(),
                "E": MemoryDataset(),
                "F": JSONDataset(filepath=template_filepath),
            }
        ),
        {},
        {"E": 64},
    ),
    (  # Test inputs injection
        [{"namespace": "n2", "outputs": "F"}, {"namespace": "n1"}],
        DataCatalog(
            {
                "n1.A": MemoryDataset(2),
                "params:n1.B": MemoryDataset(1),
                "n1.C": MemoryDataset(),
                "n1.D": MemoryDataset(),
                "n1.E": MemoryDataset(),
                "n1.F": JSONDataset(filepath=template_filepath),
                "n2.A": MemoryDataset(2),
                "params:n2.B": MemoryDataset(1),
                "n2.C": MemoryDataset(),
                "n2.D": MemoryDataset(),
                "n2.E": MemoryDataset(),
                "F": JSONDataset(filepath=template_filepath),
            }
        ),
        {"namespace": "n2", "inputs": {"A": 3}, "parameters": {"B": 1}},
        729,
    ),
    (  # Test params injection
        [{"namespace": "n2", "outputs": "F"}, {"namespace": "n1"}],
        DataCatalog(
            {
                "n1.A": MemoryDataset(2),
                "params:n1.B": MemoryDataset(1),
                "n1.C": MemoryDataset(),
                "n1.D": MemoryDataset(),
                "n1.E": MemoryDataset(),
                "n1.F": JSONDataset(filepath=template_filepath),
                "n2.A": MemoryDataset(2),
                "params:n2.B": MemoryDataset(1),
                "n2.C": MemoryDataset(),
                "n2.D": MemoryDataset(),
                "n2.E": MemoryDataset(),
                "F": JSONDataset(filepath=template_filepath),
            }
        ),
        {"namespace": "n2", "inputs": {"A": 3}, "parameters": {"B": 2}},
        46656,
    ),
    (  # Test itertime params injection
        [{"namespace": "n2", "outputs": "F"}, {"namespace": "n1"}],
        DataCatalog(
            {
                "n1.A": MemoryDataset(2),
                "params:n1.B": MemoryDataset(1),
                "n1.C": MemoryDataset(),
                "n1.D": MemoryDataset(),
                "n1.E": MemoryDataset(),
                "n1.F": JSONDataset(filepath=template_filepath),
                "n2.A": MemoryDataset(2),
                "params:n2.B": MemoryDataset(1),
                "n2.C": MemoryDataset(),
                "n2.D": MemoryDataset(),
                "n2.E": MemoryDataset(),
                "F": JSONDataset(filepath=template_filepath),
            }
        ),
        {
            "namespace": "n2",
            "inputs": {"A": 3},
            "parameters": {"B": 2},
            "itertime_params": {"date_param": 1234},
        },
        46656,
    ),
    (  # Test branching inputs between namespaces
        [
            {"namespace": "n2"},
            {"namespace": "n1", "inputs": {"A": "n2.A"}, "outputs": "F"},
        ],
        DataCatalog(
            {
                "n1.A": MemoryDataset(2),
                "params:n1.B": MemoryDataset(1),
                "n1.C": MemoryDataset(),
                "n1.D": MemoryDataset(),
                "n1.E": MemoryDataset(),
                "F": JSONDataset(filepath=template_filepath),
            },
            {
                "n2.A": MemoryDataset(4),
                "params:n2.B": MemoryDataset(1),
                "n2.C": MemoryDataset(),
                "n2.D": MemoryDataset(),
                "n2.E": MemoryDataset(),
                "n2.F": JSONDataset(filepath=template_filepath),
            },
        ),
        {"namespace": "n1", "parameters": {"B": 1}},
        4096,
    ),
]


@pytest.mark.parametrize(
    "namepsaces, catalog, render_data, expected_run_results",
    parametrized_test_session_scenarios,
)
def test_session(
    mock_pipeline: Pipeline,
    namepsaces: List[dict],
    catalog: dict,
    render_data: dict,
    expected_run_results: dict,
):
    all_pipelines = pipeline([])
    for namepsace in namepsaces:
        all_pipelines = all_pipelines + pipeline(mock_pipeline, **namepsace)

    session = KedroBootSession(
        pipeline=all_pipelines,
        catalog=catalog,
        hook_manager=_NullPluginManager(),
        session_id="test1234",
        app_runtime_params={},
        config_loader=OmegaConfigLoader(""),
    )

    # session.compile_catalog()

    results = session.run(**render_data)
    assert results
    assert results == expected_run_results


# TODO: Test that cover warning

# TODO: Tests that covers Exceptions
