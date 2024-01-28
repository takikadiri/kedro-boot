"""A CLI factory for kedro boot apps"""
import click
import logging
from pathlib import Path
from kedro.framework.startup import _is_project
from .factory import kedro_boot_command_factory
from .utils import get_entry_points_commands

LOGGER = logging.getLogger(__name__)


run_command = kedro_boot_command_factory(
    command_name="run", command_help="Run kedro boot apps"
)
compile_command = kedro_boot_command_factory(
    command_name="compile",
    command_help="Compile the catalog (Dryrun)",
    app_class="kedro_boot.app.CompileApp",
)

# Get entry points commands early to prevent getting them repeatedly inside KedroClickGroup
entry_points_commands = get_entry_points_commands("kedro_boot")


class KedroClickGroup(click.Group):
    def reset_commands(self):
        self.commands = {}

        # add commands on the fly based on conditions
        if _is_project(Path.cwd()):
            self.add_command(run_command)
            self.add_command(compile_command)
            for entry_point_command in entry_points_commands:
                self.add_command(entry_point_command)

        # else:
        #     self.add_command(new) # TODO : IMPLEMENT THIS FUNCTION

    def list_commands(self, ctx):
        self.reset_commands()
        commands_list = sorted(self.commands)
        return commands_list

    def get_command(self, ctx, cmd_name):
        self.reset_commands()
        return self.commands.get(cmd_name)


@click.group(name="Boot")
def commands():
    """Kedro plugin for integrating any application with kedro."""
    pass  # pragma: no cover


@commands.command(name="boot", cls=KedroClickGroup)
def boot_commands():
    """kedro boot specific commands inside kedro project."""
    pass  # pragma: no cover
