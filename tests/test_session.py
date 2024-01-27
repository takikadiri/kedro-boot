from kedro_boot.session import KedroBootSession, KedroBootSessionError
import pytest
from kedro.pipeline import Pipeline
from kedro_boot.pipeline import app_pipeline
from kedro.framework.hooks.manager import _NullPluginManager
from kedro.config import OmegaConfigLoader
from kedro.io import DataCatalog


parametrized_test_session_scenarios = [
    (
        {"name": "view1", "inputs": ["A"], "outputs": ["C"]},
        {"name": "view1", "inputs": {"A": 10}},
        10,
    ),
    (
        {"name": "view2", "inputs": ["A"]},
        {"name": "view2", "inputs": {"A": 10}},
        {"C": 10},
    ),
]


@pytest.mark.parametrize(
    "pipeline_view, render_data, expected_results", parametrized_test_session_scenarios
)
def test_session(
    mock_pipeline: Pipeline,
    mock_catalog: DataCatalog,
    pipeline_view: dict,
    render_data: dict,
    expected_results,
):
    test_app_pipeline = app_pipeline(
        mock_pipeline.only_nodes("identity"), **pipeline_view
    )
    session = KedroBootSession(
        pipeline=test_app_pipeline,
        catalog=mock_catalog,
        hook_manager=_NullPluginManager(),
        session_id="",
        config_loader=OmegaConfigLoader(""),
    )

    session.compile_catalog()

    results = session.run(**render_data)

    assert results
    assert results == expected_results


@pytest.mark.parametrize(
    "pipeline_view, render_data, expected_results", parametrized_test_session_scenarios
)
def test_session_lazy_compile(
    mock_pipeline: Pipeline,
    mock_catalog: DataCatalog,
    pipeline_view: dict,
    render_data: dict,
    expected_results,
):
    test_app_pipeline = app_pipeline(
        mock_pipeline.only_nodes("identity"), **pipeline_view
    )
    session = KedroBootSession(
        pipeline=test_app_pipeline,
        catalog=mock_catalog,
        hook_manager=_NullPluginManager(),
        session_id="",
        config_loader=OmegaConfigLoader(""),
    )

    results = session.run(**render_data)

    assert session._is_catalog_compiled
    assert results
    assert results == expected_results


@pytest.mark.parametrize(
    "pipeline_view, render_data, expected_results", parametrized_test_session_scenarios
)
def test_session_multi_compile(
    mock_pipeline: Pipeline,
    mock_catalog: DataCatalog,
    pipeline_view: dict,
    render_data: dict,
    expected_results,
):
    test_app_pipeline = app_pipeline(
        mock_pipeline.only_nodes("identity"), **pipeline_view
    )
    session = KedroBootSession(
        pipeline=test_app_pipeline,
        catalog=mock_catalog,
        hook_manager=_NullPluginManager(),
        session_id="",
        config_loader=OmegaConfigLoader(""),
    )

    session.run(**render_data)

    with pytest.raises(KedroBootSessionError):
        session.compile_catalog()
