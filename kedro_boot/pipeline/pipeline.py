""""``AppPipeline`` make the the kedro catalog ready for interaction with the kedro boot app."""

from typing import Iterable, List, Optional, Union

from kedro.pipeline import Pipeline
from kedro.pipeline.node import Node

from kedro_boot.pipeline.utils import find_duplicates

DEFAULT_PIPELINE_VIEW_NAME = "__default__"


class PipelineView:
    """A ``PipelineView`` view define the exposition points to the Kedro Boot application.
    It provides a perspective on the underlying pipeline, filtered by a particular tag and organized by dataset categories.
    """

    def __init__(
        self,
        name: str,
        inputs: Optional[List[str]] = None,
        outputs: Optional[List[str]] = None,
        parameters: Optional[List[str]] = None,
        artifacts: Optional[List[str]] = None,
        infer_artifacts: Optional[bool] = None,
    ) -> None:
        """Init ``PipelineView`` with a name and a categorisation of the datasets that are exposed to the app.

        Args:
            name (str): A view name. It should be unique per AppPipeline views.
            inputs (List[str]): Inputs datasets that will be injected by the app data at iteration time.
            outputs (List[str]): Outputs dataset that hold the iteration run results.
            parameters (List[str]): Parameters that will be injected by the app data at iteration time.
            artifacts (List[str]): Artifacts datasets that will be materialized (loaded as MemoryDataset) at startup time.
            infer_artifacts (bool): If no artifacts given, should we infer them dynamically. infered artifacts = pipeline inputs - (inputs + parameters + templates)
        """
        self.name = name
        self.inputs = inputs or []
        self.outputs = outputs or []
        self.parameters = parameters or []
        self.artifacts = artifacts or []
        self.infer_artifacts = False if infer_artifacts is None else infer_artifacts

    def __str__(self) -> str:
        return (
            f"PipelineView("
            f"name={self.name}, "
            f"inputs={self.inputs}, "
            f"outputs={self.outputs}, "
            f"parameters={self.parameters}, "
            f"artifacts={self.artifacts}, "
            f"infer_artifacts={self.infer_artifacts})"
        )


class AppPipeline(Pipeline):
    """A kedro Pipeline having a list of views defining the exposition points of the pipeline to the kedro boot app.

    Args:
        Pipeline (Pipeline): Kedro Pipeline
    """

    def __init__(
        self, nodes: Iterable[Union[Node, Pipeline]], *, views: List[PipelineView]
    ) -> None:
        """_summary_

        Args:
            nodes (Iterable[Node  |  Pipeline]): A collection of kedro Nodes or Pipelines
            views (List[PipelineView]): A Collection of ``PipelineView`` defining the exposition points of the pipeline for the app.

        Raises:
            AppPipelineError: _description_
        """

        super().__init__(nodes)

        view_names = [view.name for view in views]

        duplicated_views = find_duplicates(view_names)
        if duplicated_views:
            raise AppPipelineError(
                f"Cannot create an AppPipeline with duplicated view names. Those views '{duplicated_views}' are present in more that one app pipeline."
            )

        self.views = views

    def __add__(self, other):
        if isinstance(other, AppPipeline):
            views = self.views + other.views
            view_names = [view.name for view in views]
            duplicated_views = find_duplicates(view_names)
            if duplicated_views:
                raise ValueError(
                    f"Cannot Add two AppPipeline having duplicated view names. Those view names '{duplicated_views}' are present in both app pipelines."
                )
        else:
            views = self.views

        nodes = self.nodes + other.nodes
        return AppPipeline(nodes, views=views)

    def __sub__(self, other):
        raise NotImplementedError()

    def __and__(self, other):
        raise NotImplementedError()

    def __or__(self, other):
        raise NotImplementedError()

    # Implement filter, as it's used by the kedro session run method
    def filter(
        self,
        tags: Iterable[str] = None,
        from_nodes: Iterable[str] = None,
        to_nodes: Iterable[str] = None,
        node_names: Iterable[str] = None,
        from_inputs: Iterable[str] = None,
        to_outputs: Iterable[str] = None,
        node_namespace: str = None,
    ) -> Pipeline:  # type: ignore
        pipeline = super().filter(
            tags,
            from_nodes,
            to_nodes,
            node_names,
            from_inputs,
            to_outputs,
            node_namespace,
        )  # type: ignore
        return AppPipeline(pipeline.nodes, views=self.views)

    def get_view(self, name: str) -> PipelineView:
        view = next(
            (view for view in self.views if view.name == name),
            None,
        )

        if not view:
            raise AppPipelineError(
                f"The given view name '{name}' is not present in the app pipeline."
            )

        return view

    def get_physical_pipeline(self, name: str) -> Pipeline:
        return self.only_nodes_with_tags(name)


class AppPipelineError(Exception):
    """Error raised in AppPipeline operations"""
