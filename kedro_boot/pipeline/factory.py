""" A factory for creating AppPipeline instances."""
import copy
import logging
from itertools import chain
from typing import Iterable, List, Optional, Union

from kedro.pipeline import Pipeline
from kedro.pipeline.modular_pipeline import pipeline
from kedro.pipeline.node import Node, node

from .pipeline import DEFAULT_PIPELINE_VIEW_NAME, AppPipeline, PipelineView
from .utils import find_duplicates

LOGGER = logging.getLogger(__name__)


def app_pipeline(
    pipe: Union[Iterable[Union[Pipeline, AppPipeline]], Pipeline, AppPipeline],
    *,
    name: Optional[str] = None,
    inputs: Optional[Union[str, List[str]]] = None,
    outputs: Optional[Union[str, List[str]]] = None,
    parameters: Optional[Union[str, List[str]]] = None,
    artifacts: Optional[Union[str, List[str]]] = None,
    infer_artifacts: Optional[bool] = None,
) -> AppPipeline:
    r"""Create a ``AppPipeline`` from a collection of ``Pipeline`` or ``AppPipeline``.

    Args:
        pipe: The pipelines the ``AppPipeline`` will be made of.
        inputs: A name or collection of input names to be exposed as connection points to kedro boot app.
            The kedro boot app will inject data to thoses inputs at each run iteration, refering to them by their names without explicitly including namespace prefix (if any).
            Must only refer to the pipeline's free inputs.
        outputs: A name or collection of output names to be exposed as connection points to the kedro boot app.
            The kedro boot app will load those datasets at each run iteration.
            Can refer to both the pipeline's free outputs, as well as intermediate results that need to be exposed.
        parameters: A name or collection of parameter names that are exposed to the kedro boot app.
            The kedro boot app will inject new parameters into those parameters at each run iteration.
            The parameters can be specified without the `params:` prefix.
        artifacts: A name or collection of artifact names.
            Artifacts are the datasets that will be materialized (loaded as MemoryDataset) at startup time, so they can be reused at each run iteration without the I/O cost.
            Must only refer to the pipeline's free inputs.
        infer_artifacts: If no artifacts given, should we infer them dynamically. infered artifacts = pipeline free inputs - (view inputs + view parameters + view templates)


    Raises:
        AppPipelineFactoryError: __description__

    Returns:
        A new ``AppPipeline`` object.
    """

    pipelines = copy.copy(pipe)
    if not isinstance(pipelines, Iterable):
        pipelines = [pipelines]

    views = list(
        chain.from_iterable(
            [
                pipeline.views
                for pipeline in pipelines
                if isinstance(pipeline, AppPipeline)
            ]  # type: ignore
        )
    )

    view_names = [view.name for view in views]
    duplicated_views = find_duplicates(view_names)
    if duplicated_views:
        raise ValueError(
            f"Cannot create an AppPipeline with duplicated view names. Those view names '{duplicated_views}' are present in more that one given app pipeline."
        )

    pipeline_view_name = name or DEFAULT_PIPELINE_VIEW_NAME

    formated_inputs = _format_dataset_names(inputs)
    formated_outputs = _format_dataset_names(outputs)
    formated_parameters = _format_dataset_names(parameters)
    formated_artifacts = _format_dataset_names(artifacts)

    formated_infer_artifacts = False if infer_artifacts is None else infer_artifacts

    if artifacts and formated_infer_artifacts:
        LOGGER.info("you've gived an artifacts set, infer_artifacts will be ignored")
        formated_infer_artifacts = False

    _check_if_tag_exist(pipelines, pipeline_view_name)
    modular_pipeline = pipeline(
        pipe=pipelines,
        inputs=(set(formated_inputs) | set(formated_artifacts)),
        outputs=set(formated_outputs),
        parameters=set(formated_parameters),
        tags=pipeline_view_name,
    )

    views.append(
        PipelineView(
            name=pipeline_view_name,
            inputs=formated_inputs,
            outputs=formated_outputs,
            parameters=formated_parameters,
            artifacts=formated_artifacts,
            infer_artifacts=formated_infer_artifacts,
        )
    )

    return AppPipeline([modular_pipeline], views=views)


def _check_if_tag_exist(pipelines: Iterable[Union[Node, Pipeline]], tag: str) -> None:
    for pipe in pipelines:
        if isinstance(pipe, Pipeline):
            nodes = pipe.nodes
        else:
            nodes = [pipe]  # pipe is a Node

        for pipe_node in nodes:
            if tag in pipe_node.tags:
                raise AppPipelineFactoryError(
                    f"Cannot create an app pipeline with a name '{tag}' as it's already used in the underlying pipeline's nodes. Please consider renaming the app pipeline or removing the tag name from the underlying pipeline's nodes."
                )


def _format_dataset_names(ds_name) -> List[str]:
    if not ds_name:
        return []
    if isinstance(ds_name, str):
        return [ds_name]
    if isinstance(ds_name, list):
        return list(set(ds_name))

    return list(ds_name)


# Can be used when a kedro boot app does not need kedro pipelines.
def create_dummy_pipeline():
    def dummy_func(dummy_input):
        pass

    dummy_node = node(dummy_func, "dummy_input", None)
    return Pipeline([dummy_node])


class AppPipelineFactoryError(Exception):
    """Error raised in AppPipeline factory operations"""
