import pytest
from kedro_boot.catalog import AppCatalog
from kedro_boot.catalog.view import CatalogView
from kedro_boot.pipeline.factory import (
    app_pipeline,
)  # Replace 'your_module' with the actual module name
from kedro.io import MemoryDataSet
from kedro.pipeline import Pipeline
from kedro.extras.datasets.pandas import CSVDataSet
from pathlib import PurePath
from kedro_boot.catalog.renderer import CatalogRendererError

# parametrized pipeline views
parametrized_pipeline_views = [
    (
        {"name": "view1", "inputs": ["A"], "outputs": ["C"]},
        {
            "name": "view1",
            "inputs": {"A": MemoryDataSet(1)},
            "outputs": {"C": MemoryDataSet(3)},
            "parameters": {},
            "artifacts": {},
            "templates": {"D": CSVDataSet("data/01_raw/test_data_[[ data_date ]].csv")},
            "unmanaged": {"B": MemoryDataSet(2)},
        },
    ),
    (
        {"name": "view2", "inputs": ["A"], "artifacts": "B", "outputs": ["C"]},
        {
            "name": "view2",
            "inputs": {"A": MemoryDataSet(1)},
            "outputs": {"C": MemoryDataSet(3)},
            "parameters": {},
            "artifacts": {"B": MemoryDataSet(2)},
            "templates": {"D": CSVDataSet("data/01_raw/test_data_[[ data_date ]].csv")},
            "unmanaged": {},
        },
    ),
]


@pytest.mark.parametrize(
    "pipeline_view, expected_catalog_view", parametrized_pipeline_views
)
def test_compile(
    mock_pipeline: Pipeline,
    mock_app_catalog: AppCatalog,
    pipeline_view: dict,
    expected_catalog_view,
):
    # Create an AppPipeline (you may need to mock this) and call 'compile'

    test_app_pipeline = app_pipeline(mock_pipeline, **pipeline_view)
    mock_app_catalog.compile(test_app_pipeline)

    # Assert that catalog_views is not empty
    assert mock_app_catalog.catalog_views
    assert mock_app_catalog.catalog_views[0].name == expected_catalog_view["name"]
    assert (
        mock_app_catalog.catalog_views[0].inputs.keys()
        == expected_catalog_view["inputs"].keys()
    )
    assert (
        mock_app_catalog.catalog_views[0].outputs.keys()
        == expected_catalog_view["outputs"].keys()
    )
    assert (
        mock_app_catalog.catalog_views[0].parameters.keys()
        == expected_catalog_view["parameters"].keys()
    )
    assert (
        mock_app_catalog.catalog_views[0].artifacts.keys()
        == expected_catalog_view["artifacts"].keys()
    )
    assert (
        mock_app_catalog.catalog_views[0].templates.keys()
        == expected_catalog_view["templates"].keys()
    )
    assert (
        mock_app_catalog.catalog_views[0].unmanaged.keys()
        == expected_catalog_view["unmanaged"].keys()
    )


@pytest.mark.parametrize(
    "pipeline_view, render_data, expected_rendered_catalog",
    [
        (
            {"name": "view1", "inputs": ["A"]},
            {
                "name": "view1",
                "inputs": {"A": 10},
                "template_params": {"date_param": "01-01-1960"},
            },
            {"A": 10, "D": "data/01_raw/test_data_01-01-1960.csv"},
        )
    ],
)
def test_render_catalog(
    mock_pipeline: Pipeline,
    mock_app_catalog: AppCatalog,
    pipeline_view: dict,
    render_data: dict,
    expected_rendered_catalog: dict,
):
    test_app_pipeline = app_pipeline(mock_pipeline, **pipeline_view)
    mock_app_catalog.compile(test_app_pipeline)

    # Call the 'render' method with required parameters
    rendered_catalog = mock_app_catalog.render(**render_data)

    assert len(rendered_catalog.list()) == len(test_app_pipeline.data_sets())

    assert rendered_catalog._data_sets["A"]._data == expected_rendered_catalog["A"]
    assert rendered_catalog._data_sets["D"]._filepath == PurePath(
        expected_rendered_catalog["D"]
    )

    # Assert that the rendered_catalog is not empty
    assert rendered_catalog


def test_render_catalog_without_suffisent_inputs(
    mock_pipeline: Pipeline, mock_app_catalog: AppCatalog
):
    test_app_pipeline = app_pipeline(mock_pipeline, name="view", inputs=["A"])
    mock_app_catalog.compile(test_app_pipeline)

    # Call the 'render' method with required parameters
    with pytest.raises(CatalogRendererError):
        mock_app_catalog.render(name="view")


# Test the 'get_catalog_view' method
def test_get_catalog_view(mock_app_catalog: AppCatalog):
    # Create a mock catalog view and add it to app_catalog
    mock_catalog_view = CatalogView(name="mock_view")
    mock_app_catalog.catalog_views.append(mock_catalog_view)

    # Call 'get_catalog_view' for the added view
    retrieved_view = mock_app_catalog.get_catalog_view("mock_view")

    # Assert that the retrieved view is the same as the mock_catalog_view
    assert retrieved_view == mock_catalog_view


# Test the 'get_view_names' method
def test_get_view_names(mock_app_catalog: AppCatalog):
    # Create mock catalog views and add them to app_catalog
    mock_app_catalog.catalog_views.append(CatalogView(name="view1"))
    mock_app_catalog.catalog_views.append(CatalogView(name="view2"))

    # Call 'get_view_names' and check the returned list
    view_names = mock_app_catalog.get_view_names()

    # Assert that the list of view names matches the added views
    assert view_names == ["view1", "view2"]
