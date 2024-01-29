import click
from kedro_boot.app.fastapi import FastApiApp
from kedro_boot.framework.cli import kedro_boot_command_factory

app_params = [
    click.option("--app", type=str, help="fastapi app"),
    click.option("--host", type=str, help="fastapi host"),
    click.option("--port", type=int, help="fastapi port"),
    click.option("--workers", type=int, help="number of workers"),
]

fastapi_command = kedro_boot_command_factory(
    command_name="fastapi",
    command_help="Serve a kedro pipeline using a fastapi app",
    app_class=FastApiApp,
    command_params=app_params,
)
