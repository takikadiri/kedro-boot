"""A CLI factory for kedro boot apps"""

import logging
from typing import Any, Callable, List, Optional, Union

import click
from click import Command
from click.decorators import FC
from kedro.framework.cli.project import run as kedro_run_command
from kedro.framework.session import KedroSession
from kedro.utils import load_obj
from kedro_boot.app.app import AbstractKedroBootApp
from kedro_boot.framework.adapter import KedroBootAdapter

LOGGER = logging.getLogger(__name__)


def create_kedro_booter(
    app_class: Optional[str] = None,
    app_args: Optional[dict] = None,
    kedro_session_create_args: Optional[dict] = None,
):
    kedro_session_create_args = kedro_session_create_args or {}
    app_args = app_args or {}

    def kedro_booter(**kwargs):
        """Running kedro boot apps"""

        # ctx = click.get_current_context()
        kedro_run_params = [
            param.name.replace("-", "_") for param in kedro_run_command.params
        ]  # format params in a python supported format. Ex: replace - by _
        app_run_args = {
            arg_key: arg_value
            for arg_key, arg_value in kwargs.items()
            if arg_key not in kedro_run_params
        }
        kedro_args = {
            arg_key: arg_value
            for arg_key, arg_value in kwargs.items()
            if arg_key not in app_run_args
        }

        # Init kedro boot app object
        app = None
        if app_class:
            app = app_factory(app_class, app_args)
        else:
            cli_app_class = app_run_args.pop("app")
            if cli_app_class:
                LOGGER.info("We're gettings app class from --app CLI arg")
                app = app_factory(cli_app_class)

        tuple_tags = tuple(kedro_args.get("tags", ""))
        tuple_node_names = tuple(kedro_args.get("node_names", ""))

        with KedroSession.create(
            env=kedro_args.get("env", ""),
            extra_params=kedro_args.get("params", ""),
            conf_source=kedro_args.get("conf_source", ""),  # type: ignore
            **kedro_session_create_args,  # TODO: Make sure that this not take precedence over kedro_args. We should do some prior merging before kwarging
        ) as session:
            config_loader = session._get_config_loader()
            config_loader._register_new_resolvers(
                {
                    "itertime_params": lambda variable,
                    default_value=None: f"${{oc.select:{variable},{default_value}}}",
                }
            )
            if app:
                runner = KedroBootAdapter(
                    app=app,
                    config_loader=config_loader,
                    app_runtime_params=app_run_args,
                )
            else:
                runner_obj = load_obj(
                    kedro_args.get("runner", "") or "SequentialRunner", "kedro.runner"
                )
                runner = runner_obj(is_async=kedro_args.get("is_async", ""))

            return session.run(
                tags=tuple_tags,
                runner=runner,
                node_names=tuple_node_names,
                from_nodes=kedro_args.get("from_nodes", ""),
                to_nodes=kedro_args.get("to_nodes", ""),
                from_inputs=kedro_args.get("from_inputs", ""),
                to_outputs=kedro_args.get("to_outputs", ""),
                load_versions=kedro_args.get("load_versions", {}),
                pipeline_name=kedro_args.get("pipeline", ""),
                namespace=kedro_args.get("namespace", ""),
            )

    return kedro_booter


def kedro_boot_command_factory(
    command_name: str = None,
    command_help: str = None,
    command_params: Optional[List[Callable[[FC], FC]]] = None,
    app_class: Optional[str] = None,
    app_args: Optional[dict] = None,
    kedro_session_create_args: Optional[dict] = None,
) -> Command:
    command_name = command_name or "app"
    command_params = command_params or []

    kedro_session_create_args = kedro_session_create_args or {}
    app_args = app_args or {}

    # If no app_class given. We'll add an app Option in the Command and use DummyApp as default
    if not app_class:
        for commad_param in command_params:
            if commad_param.name == "app":
                LOGGER.warning(
                    "No app_class was given and at the same time 'app' Option is found in your kedro boot cli factory command_params. We're going to replace your app Option by kedro boot app Option. So you can have a way to provide an app_class"
                )
                command_params.remove(commad_param)
                break

        command_params.append(
            click.option(
                "--app",
                type=str,
                default="",
                help="Kedro Boot App Class. ex: my_package.my_module.my_app_class",
            )
        )

    kedro_booter = create_kedro_booter(
        app_class=app_class,
        app_args=app_args,
        kedro_session_create_args=kedro_session_create_args,
    )

    @click.command(name=command_name, short_help=command_help)
    def kedro_boot_command(**kwargs) -> Any:
        return kedro_booter(**kwargs)

    kedro_boot_command.params.extend(
        kedro_run_command.params
    )  # TODO: We should check for collisions between app params and kedro params
    for param in command_params:
        kedro_boot_command = param(kedro_boot_command)

    return kedro_boot_command


def app_factory(
    app_class: Union[str, AbstractKedroBootApp], app_args: dict = None
) -> AbstractKedroBootApp:
    app_args = app_args or {}
    if isinstance(app_class, str):
        app_class_obj = load_obj(app_class)
    else:
        app_class_obj = app_class

    if not issubclass(app_class_obj, AbstractKedroBootApp):
        raise TypeError(
            f"app_class must be a subclass of AbstractKedroBootApp, got {app_class_obj.__name__}"
        )

    return app_class_obj(**app_args) if app_args else app_class_obj()
