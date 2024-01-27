"""A CLI factory for kedro boot apps"""

import logging
from typing import Callable, List, Optional

import click
from click import Command
from click.decorators import FC
from kedro.framework.cli.project import run as kedro_run_command
from kedro.framework.cli.utils import _get_values_as_tuple
from kedro.framework.session import KedroSession

from kedro_boot.runner import KedroBootRunner

LOGGER = logging.getLogger(__name__)


def kedro_boot_cli_factory(
    app_class: Optional[str] = None,
    app_params: Optional[List[Callable[[FC], FC]]] = None,
    lazy_compile: Optional[bool] = None,
) -> Command:
    """A factory function that create a new command with all the existing kedro run options plus given app specific options.
    The command instantiate a kedro boot runner with app_class and app_args before running the kedro session.

    Args:
        app_class (str): Kedro Boot App class. ex: my_package.my_module.my_app_class
        app_params (List[Option]): Kedro Boot App click options. These options will be added to kedro run options

    Returns:
        Command: _description_
    """

    app_params = app_params or []

    # If no app_class given. We'll add an app Option in the Command and use DummyApp as default
    if not app_class:
        for app_param in app_params:
            if app_param.name == "app":
                LOGGER.warning(
                    "No app_class was given and at the same time 'app' Option is found in your kedro boot cli factory app_params. We're going to replace your app Option by kedro boot app Option. So you can have a way to provide an app_class"
                )
                app_params.remove(app_param)
                break

        app_params.append(
            click.option(
                "--app",
                type=str,
                default="kedro_boot.app.DummyApp",
                help="Kedro Boot App Class. ex: my_package.my_module.my_app_class",
            )
        )

        app_params.append(
            click.option(
                "--dry-run",
                is_flag=True,
                help="Compile the App catalog with the given project settings without running the pipeline. If used the --app and --lazy-compile options are ignored.",
            )
        )

        app_params.append(
            click.option(
                "--lazy-compile",
                is_flag=True,
                help="Compile the catalog at a specific point of the execution flow of the application. This let the app decide when to compile the catalog. This is useful in multiprocessing apps (like Gunicorn or Spark) because some datasets may not support process forking when loaded at the master process. If the app does not specify the compilation point, it would be done lazily at the first iteration run",
            )
        )

    else:
        for app_param in app_params:
            if app_param.name == "lazy_compile" and lazy_compile is not None:
                LOGGER.warning(
                    "You have given lazy_compile options in two places, your app option params, and as argument of the cli factory. The cli factory parameter will take precedence"
                )

    @click.command()
    def kedro_boot_command(**kwargs):
        """Running kedro boot apps"""

        ctx = click.get_current_context()
        kedro_run_params = [param.name for param in kedro_run_command.params]
        app_args = {
            arg_key: arg_value
            for arg_key, arg_value in ctx.params.items()
            if arg_key not in kedro_run_params
        }
        kedro_args = {
            arg_key: arg_value
            for arg_key, arg_value in kwargs.items()
            if arg_key not in app_args
        }

        # pop the app_class from app_args
        boot_app_class = app_class or app_args.pop("app")
        app_args_lazy_compile = (
            app_args.pop("lazy_compile") if "lazy_compile" in app_args else False
        )
        boot_app_lazy_compile = (
            lazy_compile if lazy_compile is not None else app_args_lazy_compile
        )
        dry_run = app_args.pop("dry_run") if "dry_run" in app_args else False
        if dry_run:
            boot_app_class = "kedro_boot.app.DryRunApp"

        tag = _get_values_as_tuple(kedro_args["tag"])
        node_names = _get_values_as_tuple(kedro_args["node_names"])

        # temporary duplicates for the plural flags
        tags = _get_values_as_tuple(kedro_args.get("tags", []))
        nodes_names = _get_values_as_tuple(kedro_args.get("nodes_names", []))

        tag = tag + tags
        node_names = node_names + nodes_names
        load_version = {
            **kedro_args["load_version"],
            **kedro_args.get("load_versions", {}),
        }

        # best effort for retrocompatibility with kedro < 0.18.5
        namespace_kwargs = (
            {"namespace": kedro_args.get("namespace")}
            if kedro_args.get("namespace")
            else {}
        )
        conf_source_kwargs = (
            {"conf_source": kedro_args.get("conf_source")}
            if kedro_args.get("conf_source")
            else {}
        )

        with KedroSession.create(
            env=kedro_args["env"],
            extra_params=kedro_args["params"],
            **conf_source_kwargs,  # type: ignore
        ) as session:
            runner_args = {"is_async": kedro_args["is_async"]}
            config_loader = session._get_config_loader()
            config_loader._register_new_resolvers(
                {
                    "itertime_params": lambda variable,
                    default_value=None: f"${{oc.select:{variable},{default_value}}}",
                }
            )
            runner = KedroBootRunner(
                config_loader=config_loader,
                app_class=boot_app_class,
                app_args=app_args,
                lazy_compile=boot_app_lazy_compile,
                **runner_args,
            )
            session.run(
                tags=tag,
                runner=runner,
                node_names=node_names,
                from_nodes=kedro_args["from_nodes"],
                to_nodes=kedro_args["to_nodes"],
                from_inputs=kedro_args["from_inputs"],
                to_outputs=kedro_args["to_outputs"],
                load_versions=load_version,
                pipeline_name=kedro_args["pipeline"],
                **namespace_kwargs,  # type: ignore
            )

    kedro_boot_command.params.extend(kedro_run_command.params)
    for param in app_params:
        kedro_boot_command = param(kedro_boot_command)

    return kedro_boot_command


kedro_boot_command = kedro_boot_cli_factory()


@click.group(name="boot")
def commands():
    pass


commands.add_command(kedro_boot_command, "boot")
