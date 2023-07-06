#!/usr/bin/python
import click
import papis.pick
from papis.document import Document
from papistui.helpers.config import (
    check_config,
    write_default_config,
    config_file_name,
    get_config,
)
from .components.selector import Screen
import re
import sys


@click.command(help="A curses based TUI for papis")
@click.option("-l", "--library", default=None, help="Name of the library.")
@click.option(
    "-c",
    "--config",
    default=None,
    help="Full path to an alternative config file to be used.",
)
@click.option(
    "-d",
    "--debug",
    is_flag=True,
    default=False,
    help='Enter debugging mode when hitting "d" key',
)
@click.help_option("--help", "-h")
def run(library, config, debug):
    """ A curses based TUI for papis """

    if not check_config(config):
        print("No configuration file found in {}".format(config_file_name(config)))
        answer = input(
            "Dow you want to create a minimal default configuration file? (Y/n)"
        )
        if answer == "" or answer.strip().lower() == "y":
            write_default_config(config)
        else:
            print("Aborting!")
            sys.exit()

    if config:
        config = get_config(config)
    else:
        config = get_config()

    if library:
        config["base"]["library"] = library

    from papistui.tui import Tui

    tui = Tui(config=config, debugging=debug)
    tui.run()


def pick(options):
    """ Run tui to pick an option from list

    :param options: list of documents from which to choose from
    :return chosen option
    """

    if len(options) == 1:
        return options[0]
    elif len(options) == 0:
        return []
    else:
        if isinstance(options[0], Document):
            from papistui.tui import Tui

            tui = Tui(options)
            selection = tui.run()
            if not selection:
                print("No document selected!")
                sys.exit()
            else:
                return selection
        else:
            display_options = [re.sub(".*/", "", i) for i in options]
            screen = Screen(display_options)
            selection = screen.run()
            return options[selection]


class Picker(papis.pick.Picker):
    def __call__(self, items, header_filter, match_filter, default_index: int = 0):
        return [pick(items)]


if __name__ == "__main__":
    run()
