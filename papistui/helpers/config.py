import os
import yaml
import papis.config

default_config = {
    "documentlist": {
        "marked-icon": "*",
        "defaultstyle": "multiline",
        "multilinestyle": {
            "rows": [
                '<red>{doc.html_escape["ref"]}</red>',
                '<bold>{doc.html_escape["title"]}<bold>',
                '<cyan>{doc.html_escape["author"]}</cyan>',
            ]
        },
        "tablestyle": {
            "separator": " │ ",
            "headerstyle": "underline|bold",
            "rowstyle": "white_bg",
            "cursorrowstyle": "black_white",
            "columns": [
                {"header": "Ref", "content": '{doc.html_escape["ref"]}', "width": 15},
                {
                    "header": "Author",
                    "content": '{doc.html_escape["author"]}',
                    "width": 30,
                },
                {"header": "Year", "content": '{doc.html_escape["year"]}', "width": 4},
                {
                    "header": "Title",
                    "content": '{doc.html_escape["title"]}',
                    "width": 400,
                },
            ],
        },
    },
    "statusbar": {
        "left": {"default": '<black_white> {info["mode_upper"]} <black_white>'},
        "right": {
            "default": '<black_white> {info["idx"]} < {info["marked"]} < {info["view"]} < {info["items"]}  <black_white>'
        },
    },
    "keymappings": {
        "j": "scroll_down",
        "k": "scroll_up",
        "<key_up>": "scroll_up",
        "<key_down>": "scroll_down",
        " ": "mark_selected",
        "q": "quit",
        "e": "edit",
        "o": "open",
        "gg": "jump_to_top",
        "G": "jump_to_bottom",
        "/": "search_mode",
        "?": "help",
    },
}


def config_file_name(file_name=None, include_path=True):
    """ Return the filename of the configuration file

    :param file_name: str force a specific filename, defaults to None and returns default
    :param include_path: bool whether to include filepath, defaults to True
    :return str filename
    """
    if not file_name:
        file_name = "papistui.yaml"
        if include_path:
            fn = os.path.join(papis.config.get_config_folder(), file_name)
    else:
        fn = file_name
    return fn


def write_default_config(file_name=None):
    """ Write a default minimal configuration file

    :param file_name: str alternative filepath, defaults to None
    """
    with open(config_file_name(file_name), "w") as outfile:
        yaml.dump(default_config, outfile, default_flow_style=False)


def check_config(file_name=None):
    """ Check whether configuration file is present

    :param file_name: str provide specific path where to look at, defaults to None
    :return bool whether file exists
    """

    return os.path.exists(config_file_name(file_name))


def complete_config(config):
    """ Make sure that all strictly necessary configuration options are set

    :param config: dict of configuration options
    :return dict with all necessary entries and default values set
    """

    # base.library
    if not config.get("base"):
        config["base"] = {}

    config["base"].setdefault("library", papis.config.get_lib_name())
    config["base"].setdefault("vimflavour", "vim")

    # documentlist
    if not config.get("documentlist"):
        config["documentlist"] = {}

    config["documentlist"].setdefault("marked-icon", "*")
    config["documentlist"].setdefault("defaultstyle", "multiline")
    config["documentlist"].setdefault("tagfield", "tags")
    config["documentlist"].setdefault("sortkeys", "")

    if "defaultsort" in config["documentlist"]:
        config["documentlist"]["defaultsort"] = config["documentlist"][
            "defaultsort"
        ].split()

    if not config["documentlist"].get("tablestyle"):
        config["documentlist"]["tablestyle"] = {}

    config["documentlist"]["tablestyle"].setdefault("separator", " │ ")
    config["documentlist"]["tablestyle"].setdefault("headerstyle", "underline|bold")
    config["documentlist"]["tablestyle"].setdefault("rowstyle", "white_bg")
    config["documentlist"]["tablestyle"].setdefault("cursorrowstyle", "black_white")

    if not config["documentlist"]["tablestyle"].get("columns"):
        config["documentlist"]["tablestyle"] = default_config["documentlist"][
            "tablestyle"
        ]["columns"]
    if not config["documentlist"].get("multilinestyle"):
        config["documentlist"]["multilinestyle"] = {}

    if not config["documentlist"]["multilinestyle"].get("rows"):
        config["documentlist"]["multilinestyle"]["rows"] = default_config[
            "documentlist"
        ]["multilinestyle"]["rows"]

    return config


def get_config(file_name=None):
    """ Load configuration file and complete it where necessary

    :param file_name: alternative file path to be used, defaults to None
    :return dict with configuration options
    """

    if os.path.exists(config_file_name(file_name)):
        with open(config_file_name(file_name), "r") as f:
            config = yaml.safe_load(f)

        return complete_config(config)
