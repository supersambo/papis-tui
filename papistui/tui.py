import re
import io
import os
import shlex
import curses
import subprocess
import tempfile
from curses.textpad import Textbox

import papis.api as api
from papis.api import open_file
from papis.api import open_dir
from papis.commands.edit import run as edit_document
from papis.commands.rm import run as rm_document
from papis.commands.browse import run as browse_document

from papistui.helpers.customargparse import ArgumentParser, HelpCall
from papistui.helpers.document import Document
from papistui.helpers.styleparser import StyleParser
from papistui.helpers.keymappings import KeyMappings
from papistui.helpers.config import get_config
from papistui.components.documentlist import DocumentList
from papistui.components.statusbar import StatusBar
from papistui.components.messagebar import MessageBar
from papistui.components.commandinfo import CommandInfo
from papistui.components.infowindow import InfoWindow
from papistui.components.keyinfo import KeyInfo
from papistui.components.helpwindow import HelpWindow
from papistui.features.vim import Vim
from papistui.features.tagging import process_tags, tag_document


try:
    # this was introduced recently
    from papis.logging import setup as setup_logging
    # This is used to redirect papis logger to a temporary file
    # in order to avoid it messing up curses when printing to stdout
    tmpfile = tempfile.NamedTemporaryFile()
    setup_logging(50, logfile = tmpfile.name)

except:
    pass



class Tui(object):
    def __init__(self, options=None, config=None, debugging=False):
        """ Constructor method

        :param options: list of documents, defaults to None
        :param config: dict configuration options, defaults to None
        :param debugging: bool whether to allow entering degbugger when hitting d, defaults to False
        """

        self._quit = False
        self.lock = False
        self._mode = "normal"
        self._message = None
        self.debugging = debugging
        self.picker = True if options else False
        self.picked = False
        self.prefix = {"command": ":", "search": "/", "select": ":"}

        # config
        if config:
            self.config = config
        else:
            self.config = get_config()
        self.km = KeyMappings(self.config)
        self.keymappings = self.config["keymappings"]
        self.keychain = []

        # curses
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        self.setcolors()
        self.styleparser = StyleParser()

        # MessageBar
        self.messagebar = MessageBar(self.stdscr)

        # CommandInfo
        self.commandinfo = CommandInfo(self.stdscr)
        self.command = None

        # InfoWindow
        self.infowindow = InfoWindow(self.stdscr, self.config)

        # calculate component sizes
        self.calcsize()

        # Documentlist
        self.library = self.config["base"]["library"]
        if options:
            docs = options
        else:
            docs = self.getalldocs()
        self.doclist = DocumentList(docs, self.doclist_size, self.stdscr, self.config)

        # tags
        self.tagfield = self.config["documentlist"]["tagfield"]

        # pass doclist to infowindow
        self.infowindow.doclist = self.doclist

        # KeyInfo
        self.keyinfo = KeyInfo(self.stdscr)

        # StatusBar
        self.statusbar = StatusBar(self.statusbar_size, self.stdscr, self.config)

        # CommandLine
        self.argstream = io.StringIO("", "\n")
        self.commandwin = curses.newwin(
            self.commandwin_size["sizey"],
            self.commandwin_size["sizex"],
            self.commandwin_size["posy"],
            self.commandwin_size["posx"],
        )
        # self.commandbox = curses.textpad.Textbox(self.commandwin)
        self.commandbox = Textbox(self.commandwin, insert_mode = True)
        self.setup_parser()

        # HelpWindow
        self.helpwindow = HelpWindow(
            stdscr=self.stdscr,
            keymappings=self.km,
            commandparser=self.commandparser,
            docpad=self.doclist.pad,
        )

        # vim connection
        self.vim = Vim(self.config["base"]["vimflavour"])

        # logfile
        # logpath = os.path.join(os.path.expanduser("~"), ".papistui.log")
        # self.logfile  = open(logpath, "w")

    def log(self, msg):
        """ Write to logfile (currently not used)

        :param msg: str message
        """
        self.logfile.write(msg)
        self.logfile.flush()

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        self._mode = mode
        if not self.helpwindow.active:
            self.statusbar.mode = mode
            self.statusbar.info = self.doclist.getinfo()

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, message):
        """ Display message in mesagebar

        :param message: str or tuple containing message (and messagetype)
        """
        self.messagebar.size = {
            "sizey": 1,
            "sizex": self.cols,
            "posy": self.rows - 3,
            "posx": 0,
        }
        self.messagebar.display(message)

    def getalldocs(self):
        """ Retrieve all documents from library

        :return list of documents
        """

        docs = api.get_all_documents_in_lib(self.library)[::-1]
        return docs

    def setcolors(self):
        """ Setup curses colors (use curses colors) """
        curses.start_color()
        curses.use_default_colors()

    def calcsize(self):
        """ Compute sizes for each component based on screen size and active components """

        rows, cols = self.stdscr.getmaxyx()
        self.rows = rows
        self.cols = cols
        self.doclist_size = {
            "sizey": rows
            - self.commandinfo.size["sizey"]
            - self.infowindow.size["sizey"]
            - 3,
            "sizex": cols,
            "posy": 0,
            "posx": 0,
        }
        self.infowindow_size = {
            "sizey": self.infowindow.size["sizey"],
            "sizex": cols,
            "posy": self.doclist_size["sizey"],
            "posx": 0,
        }
        self.statusbar_size = {
            "sizey": 1,
            "sizex": cols,
            "posy": rows - self.commandinfo.size["sizey"] - 2,
            "posx": 0,
        }
        self.commandwin_size = {"sizey": 1, "sizex": cols, "posy": rows - 1, "posx": 0}

    def resize(self):
        """ Resize all components if screen has minimal size """

        self.stdscr.erase()
        self.stdscr.refresh()
        self.calcsize()
        if self.cols > 15 and self.rows > 10:
            self.lock = False
            self.commandwin.mvwin(
                self.commandwin_size["posy"], self.commandwin_size["posx"]
            )
            self.commandwin.refresh()
            self.doclist.size = self.doclist_size
            self.statusbar.size = self.statusbar_size
            self.infowindow.size = self.infowindow_size
        else:
            self.stdscr.erase()
            self.stdscr.refresh()
            self.lock = True

    def clean(self):
        """ Clean commandinfo and messagebar """

        if self.commandinfo.active:
            self.commandinfo.destroy()
            self.resize()

        if self.messagebar.active:
            self.messagebar.destroy()
            self.resize()

    def debug(self):
        """ Enter debug mode """
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()
        import pdb

        pdb.set_trace()

    def scroll_down(self, *args):
        """ Scroll down in documentlist or helpwindow

        :return dict with exit status
        """

        if self.helpwindow.active:
            self.helpwindow.scroll_down()
        else:
            self.doclist.scroll_down()
        return {"exit_status": 0}

    def scroll_up(self, *args):
        """ Scroll up in documentlist or helpwindow

        :return dict with exit status
        """
        if self.helpwindow.active:
            self.helpwindow.scroll_up()
        else:
            self.doclist.scroll_up()
        return {"exit_status": 0}

    def info_toggle(self, *args):
        """ Toggle info window on or off

        :return dict with exit status
        """

        if not self.infowindow.enabled:
            return {"exit_status": 2, "message": ("No info views configured", "error")}
        if self.infowindow.active:
            self.infowindow.deactivate()
        else:
            self.infowindow.activate()
        self.resize()
        return {"exit_status": 0}

    def info_cycle(self, *args):
        """ Cycle through info views defined in configuration file

        :return dict with exit status
        """

        self.infowindow.next_view()
        self.resize()
        return {"exit_status": 0}

    def jump_to_bottom(self, *args):
        """ Jump to last line in documentlist or help window

        :return dict with exit status
        """
        if self.helpwindow.active:
            self.helpwindow.jump_to_bottom()
        else:
            self.doclist.jump_to_bottom()
        return {"exit_status": 0}

    def jump_to_top(self, *args):
        """ Jump to first line in documentlist or help window

        :return dict with exit status
        """
        if self.helpwindow.active:
            self.helpwindow.jump_to_top()
        else:
            self.doclist.jump_to_top()
        return {"exit_status": 0}

    def commandedit(self, fill=""):
        """ Fill commandwindow with string

        :param fill: str to be put on commandwindow, defaults to ""
        """
        self.commandwin.erase()
        curses.curs_set(2)
        self.commandwin.addstr(0, 0, self.prefix[self.mode] + fill)
        text = self.commandbox.edit(self._awaitenter)
        self.commandwin.refresh()

    def _awaitenter(self, x):
        """ Helper function to be used in commandwin Textbox

        :param x: key to be passed in by Textbox
        """

        if x == 10 or x == 13 or x == curses.KEY_ENTER:
            if self.mode == "command":
                self.handle_command(self.commandbox.gather()[1:])
            elif self.mode == "search":
                command = "search {}".format(self.commandbox.gather().strip()[1:])
                self.handle_command(command)
            elif self.mode == "select":
                option = self.commandbox.gather()[1:]
                command = "{} -o {}".format(self.command, option)
                self.command = None
                self.handle_command(command)

            self.commandwin.erase()
            self.mode = "normal"
            curses.curs_set(0)

        if x == 27:
            self.commandwin.erase()
            self.mode = "normal"
            curses.curs_set(0)

        return x

    def run(self):
        """ Main function

        :returns picked document if started as picker
        """

        try:
            self.input_stream()
        except KeyboardInterrupt:
            pass
        finally:
            curses.endwin()
            if self.picker and self.picked:
                return self.doclist.selected_doc

    def input_stream(self):
        """ Handle all input including keys and resize """

        self.statusbar.info = self.doclist.getinfo()
        self.doclist.display()
        if self.config["infowindow"]["default_on"]:
            self.info_toggle()
        while True:
            ch = self.doclist.pad.getch()
            if ch == curses.KEY_RESIZE:
                self.resize()
            if ch == ord(":"):
                self.command_mode()
                ch = None
            elif ch == curses.KEY_ENTER or ch == 10 or ch == 13:
                if self.picker:
                    self.picked = True
                    break
            elif ch == ord("d") and self.debugging:
                self.debug()

            if ch and not self.lock:
                self.handle_keypress(ch)
                if not self.helpwindow.active:
                    self.statusbar.info = self.doclist.getinfo()

            if self._quit:
                break

    def handle_keypress(self, ch):
        """ Handle keypres by either raising keyinfo, executing command or passing

        :param ch: keycode
        """

        key = [ch] if len(self.keychain) == 0 else self.keychain + [ch]
        match = self.km.match(key)
        if match:
            self.clean()
            self.keychain = []
            self.handle_command(match["cmd"])
            if not self.helpwindow.active:
                self.helpwindow.active = False
        else:
            options = self.km.find(key)
            if len(options) > 0:
                self.keychain = key
                if not self.helpwindow.active:
                    self.keyinfo.display(self.doclist, options)
            else:
                self.keychain = []
                self.commandinfo.destroy()
                self.helpwindow.active = False

    def quit(self, *args):
        """ Quit tui or helpwindow if active """

        if self.helpwindow.active:
            self.helpwindow.active = False
            self.resize()
        else:
            self._quit = True

    def command_mode(self, *args):
        """ Change into command mode and enter textbox

        :return dict with exit status
        """

        self.mode = "command"
        self.commandedit()
        return {"exit_status": 0}

    def select_mode(self, default="", *args):
        """ Change into select mode and enter texbox

        :param default: str to prefill textbox, defaults to ""
        :return dict with exit status
        """

        self.mode = "select"
        self.commandedit(fill=default)
        return {"exit_status": 0}

    def search_mode(self, *args):
        """ Change into search mode and enter texbox

        :return dict with exit status
        """

        self.mode = "search"
        self.commandedit()
        return {"exit_status": 0}

    def raise_helpwindow(self, *args):
        """ Display Helpwindow """

        self.helpwindow.display()
        return {"exit_status": 0}

    def search(self, args=None):
        """ Search for documents

        :return list of matching documents
        """

        if args:
            query = " ".join(vars(args)["query"])
            return self.doclist.docmatch(query=query)

    def sort(self, args=None):
        """ Sort documents

        :return list of sorted documents
        """

        if args:
            return self.doclist.sort(sortkeys=vars(args)["sortkeys"])

    def open(self, args):
        """ Implementation of the papis open command

        :return dict with exit status
        """

        doc = self.doclist.selected_doc
        args = vars(args)
        if args["dir"]:
            doc_folder = doc.get_main_folder()
            if doc_folder is None:
                return {"exit_status": 2, "message": ("No folder attached!", "error")}
            else:
                curses.endwin()
                open_dir(doc_folder)
                self.stdscr.refresh()
                return {"exit_status": 0}
        else:
            files = doc.get_files()
            if args["regex"] is not None:
                files = [file for file in files if re.search(args["regex"], file)]

            if args["option"] is not None:
                selection = files[int(args["option"])]
                curses.endwin()
                open_file(selection)
                self.stdscr.refresh()
                return {"exit_status": 0}
            else:
                if len(files) == 1:
                    curses.endwin()
                    open_file(files[0])
                    self.stdscr.refresh()
                    return {"exit_status": 0}
                elif len(files) > 1:
                    options = ["Choose file to open:"]
                    [
                        options.append("{}: {}".format(idx, os.path.basename(i)))
                        for idx, i in enumerate(files)
                    ]
                    return {"exit_status": 1, "options": options, "default": "0"}
                else:
                    return {
                        "exit_status": 2,
                        "message": ("No (matching) documents attached!", "error"),
                    }

    def edit(self, *args):
        """ Implementation of the papis edit command

        :return dict with exit status
        """

        curses.endwin()
        edit_document(self.doclist.selected_doc)
        self.stdscr.refresh()
        return {"exit_status": 0}

    def browse(self, *args):
        """ Implementation of the papis browse command

        :return dict with exit status
        """

        curses.endwin()
        browse_document(self.doclist.selected_doc)
        self.stdscr.refresh()
        self.resize()
        return {"exit_status": 0}

    def reload(self, *args):
        """ Reload all documents from library into documentlist

        :return dict with exit status
        """

        self.doclist.items = self.getalldocs()
        return {"exit_status": 0}

    def rm(self, args):
        """ Implementation of papis rm command (incomplete)

        :return dict with exit status
        """

        args = vars(args)
        docs = self.doclist.marked_or_selected_docs()
        if args["selected"]:
            docs = [self.doclist.selected_doc]
        len_docs = len(docs)
        if args["option"] is not None:
            if args["option"] == 1:
                for doc in docs:
                    rm_document(doc)

                self.doclist.items = self.getalldocs()
                return {"exit_status": 0, "message": ("{} document(s) deleted!".format(len_docs), "success")}
            else:
                return {"exit_status": 0, "message": ("Deletion cancelled", "error")}
        else:
            options = [
                "Are you sure you want do delete {} document(s)?".format(len_docs),
                "0: No, cancel",
                "1: Yes",
            ]
            return {"exit_status": 1, "options": options}

    def vim_connect(self, args=None):
        """ Connect to a vim server

        :return dict with exit status
        """

        servers = self.vim.get_servers()

        args = vars(args)
        if args["option"] is not None:
            self.message = args["option"]
            selection = int(args["option"])
            self.vim.set_server(servers[selection])
            return {
                "exit_status": 0,
                "message": (
                    "Vim Server set to: {}".format(self.vim.servername),
                    "success",
                ),
            }
        else:
            if len(servers) == 1:
                self.vim.set_server(servers[0])
                return {
                    "exit_status": 0,
                    "message": (
                        "Vim Server set to: {}".format(self.vim.servername),
                        "success",
                    ),
                }
            if len(servers) > 1:
                options = ["Choose server to connect to:"]
                [
                    options.append("{}: {}".format(idx, i))
                    for idx, i in enumerate(servers)
                ]
                return {"exit_status": 1, "options": options}
            else:
                return {"exit_status": 2, "message": ("No vim servers found!", "error")}

    def vim_send(self, args=None):
        """ Evaluate and send string to vim server

        :return dict with exit status
        """

        if self.vim.servername is None:
            self.handle_command("vim_connect")

        if not self.vim.check_server():
            return {
                "exit_status": 2,
                "message": ("Server not available. Please (re)connect", "error"),
            }

        args = vars(args)
        if args["string"] is not None:
            string = self.styleparser.evaluate(
                " ".join(args['string']), doc=self.doclist.selected_doc
            )
            self.vim.send(string)

    def cmd(self, args=None):
        """ Put string on command line

        :returns dict with exit status
        """

        args = vars(args)
        if args["search"]:
            self.mode = "search"
        else:
            self.mode = "command"
        if args["string"] is not None:
            string = " ".join(args["string"])
            self.commandedit(fill=string)

        return {"exit_status": 0}

    def copy_to_clipboard(self, args=None):
        """ Evaluate string and copy it to clipboard

        :returns dict with exit status
        """

        args = vars(args)
        if args["string"] is not None:
            string = " ".join(args["string"])
            value = self.styleparser.evaluate(
                string, doc=self.doclist.selected_doc
            )
            if value == "":
                return {"exit_status": 2, "message": ("Nothing to copy", "error")}
            else:
                try:
                    import pyperclip

                    pyperclip.copy(value)
                    return {
                        "exit_status": 0,
                        "message": ("Copied string to clipboard", "success"),
                    }
                except ImportError:
                    return {
                        "exit_status": 2,
                        "message": ("pyperclip is not available", "error"),
                    }
        else:
            return {
                "exit_status": 2,
                "message": ("Please provide a string to copy", "error"),
            }

    def handle_command(self, command):
        """ Tries to execute a command and handles response

        :param command: str command to be executed
        """
        if command.startswith("papis "):
            self.papis_cmd(command)
        else:
            commands = shlex.split(command.strip())
            try:
                args = self.commandparser.parse_args(commands)
                result = args.func(args)  # call the default function
                if result is None:  # try to avoid by returning exit status
                    self.commandinfo.destroy()
                    if not self.helpwindow.active:
                        self.doclist.display()
                        self.statusbar.info = self.doclist.getinfo()
                    if self.infowindow.active:
                        self.infowindow.display()
                elif result["exit_status"] == 0:
                    if not self.helpwindow.active:
                        if self.mode == "select":
                            self.commandinfo.destroy()
                            self.resize()
                        self.mode = "normal"

                        self.doclist.display()
                        self.statusbar.info = self.doclist.getinfo()
                        if self.infowindow.active:
                            self.infowindow.display()
                        if "message" in result:
                            self.message = result["message"]
                        elif self.messagebar.active:
                            self.messagebar.destroy()
                elif result["exit_status"] == 1:
                    self.command = command
                    self.raise_commandinfo(info=result["options"])
                    default = result["default"] if "default" in result else ""
                    self.select_mode(default=default)
                elif result["exit_status"] == 2:
                    self.commandinfo.destroy()
                    self.resize()
                    self.mode = "normal"
                    self.message = result["message"]

            except HelpCall as h:
                self.raise_commandinfo(info=h.helpmessage())
            except Exception as error:
                self.commandinfo.destroy()
                self.resize()
                self.doclist.display()
                info = str(error).splitlines()[0]
                info = re.sub("\(.*$", "", info)
                self.message = (info, "error")

    def raise_commandinfo(self, info):
        """
        Raises command win and displays info
        Typically either help returned from argparse or options menu

        :param info: list of strings to be displayed
        """

        if len(info) > 0:
            self.commandinfo.size = {
                "sizey": len(info),
                "sizex": self.cols,
                "posy": self.rows - len(info) - 1,
                "posx": 0,
            }
            self.resize()
            self.commandinfo.display(info)

    def tag(self, args = None):
        """ Tag marked or selected documents

        :returns dict with exit status
        """

        args = vars(args)
        docs = self.doclist.marked_or_selected_docs()
        if args["selected"]:
            docs = [self.doclist.selected_doc]
        tags = process_tags(args["tags"])
        for doc in docs:
            tag_document(doc, tags, self.tagfield)

        return {"exit_status": 0}

    def papis_cmd(self, command):
        """ Run a papis command

        :returns dict with exit status
        """
        string = self.styleparser.evaluate(command, doc=self.doclist.selected_doc, docs=self.doclist.marked)
        cmd = shlex.split(string)

        curses.endwin()
        try:
            run = subprocess.Popen(cmd, shell = False)
            run.wait()
            self.stdscr.refresh()
        except:
            self.stdscr.refresh()
            self.resize()
            self.doclist.display()
            self.message = ("Execution of papis command failed", "error")

    def setup_parser(self):
        """ Registers all the available commands to an argparse subparser """

        parser = ArgumentParser(prog="papistui", usage=None)
        subparsers = parser.add_subparsers()

        toggle_style = subparsers.add_parser(
            "toggle_style",
            description="Toggle between display styles multiline and table",
        )
        toggle_style.set_defaults(func=self.doclist.togglestyle)

        quit_ = subparsers.add_parser(
            "quit", description="Quit programme", aliases=["q"]
        )
        quit_.set_defaults(func=self.quit)

        scroll_down = subparsers.add_parser(
            "scroll_down", description="Scroll down in document list"
        )
        scroll_down.set_defaults(func=self.scroll_down)

        scroll_up = subparsers.add_parser(
            "scroll_up", description="Scroll up in document list"
        )
        scroll_up.set_defaults(func=self.scroll_up)

        page_up = subparsers.add_parser(
            "page_up", description="Page up in document list"
        )
        page_up.set_defaults(func=self.doclist.page_up)

        page_down = subparsers.add_parser(
            "page_down", description="Page down in document list"
        )
        page_down.set_defaults(func=self.doclist.page_down)

        jump_to_top = subparsers.add_parser(
            "jump_to_top", description="Jump to first document in document list"
        )
        jump_to_top.set_defaults(func=self.jump_to_top)

        jump_to_bottom = subparsers.add_parser(
            "jump_to_bottom", description="Jump to last document in document list"
        )
        jump_to_bottom.set_defaults(func=self.jump_to_bottom)

        mark_selected = subparsers.add_parser(
            "mark_selected",
            description="Toggle mark on selected document in document list",
        )
        mark_selected.set_defaults(func=self.doclist.mark_selected)

        mark_down = subparsers.add_parser(
            "mark_down",
            description="Toggle mark on selected document in document list and scroll down",
        )
        mark_down.set_defaults(func=self.doclist.mark_down)

        view_reset = subparsers.add_parser(
            "view_reset",
            description="Reset view in document list to display all documents",
        )
        view_reset.set_defaults(func=self.doclist.view_reset)

        view_marked = subparsers.add_parser(
            "view_marked", description="Set view to display only marked documents"
        )
        view_marked.set_defaults(func=self.doclist.view_marked)

        mark_view = subparsers.add_parser(
            "mark_view", description="Mark all documents in current view"
        )
        mark_view.set_defaults(func=self.doclist.mark_view)

        unmark_all = subparsers.add_parser(
            "unmark_all", description="Unmark all marked documents"
        )
        unmark_all.set_defaults(func=self.doclist.unmark_all)

        command_mode = subparsers.add_parser(
            "command_mode", description="Enter command mode"
        )
        command_mode.set_defaults(func=self.command_mode)

        search_mode = subparsers.add_parser(
            "search_mode", description="Enter search mode"
        )
        search_mode.set_defaults(func=self.search_mode)

        search = subparsers.add_parser("search", description="Search for documents")
        search.add_argument(
            "query", help="Query for searching documents", nargs="+", type=str
        )
        search.set_defaults(func=self.search)

        sort = subparsers.add_parser("sort", description="Sort documents")
        sort.add_argument(
            "sortkeys",
            help="Keys for sorting documents (e.g. year- author+)",
            nargs="+",
            type=str,
        )
        sort.set_defaults(func=self.sort)

        tag = subparsers.add_parser("tag", description="Tag marked (if any) or selected document(s)")
        tag.add_argument(
            "tags",
            help="Tags to be added or removed (by adding trailing \'-\') documents (e.g. interesting- boring+)",
            nargs="+",
            type=str,
        )
        tag.add_argument("-s", "--selected", help="Force to tag only selected document even if some are marked.", action="store_true")
        tag.set_defaults(func=self.tag)

        papis_cmd = subparsers.add_parser("papis", description="Run a papis command")
        papis_cmd.add_argument(
            "cmd",
            help="Command arguments",
            nargs="+",
            type=str,
        )
        papis_cmd.set_defaults(func=self.papis_cmd)

        opn = subparsers.add_parser(
            "open", description="Open file attached to document"
        )
        opn.add_argument(
            "-o", "--option", help="Provide an integer to select given option", type=int
        )
        opn.add_argument(
            "-r",
            "--regex",
            help="Provide regular expression to filter options",
            type=str,
        )
        opn.add_argument("-d", "--dir", help="Open directory", action="store_true")
        opn.set_defaults(func=self.open)

        vim_connect = subparsers.add_parser(
            "vim_connect", description="Look for vim servers and connect"
        )
        vim_connect.add_argument(
            "-o", "--option", help="Provide an integer to select given option", type=int
        )
        vim_connect.set_defaults(func=self.vim_connect)

        vim_send = subparsers.add_parser(
            "vim_send", description="Send string to vim server"
        )
        vim_send.add_argument(
            "string", nargs="+", help="A string to be evaluated and sent", type=str
        )
        vim_send.set_defaults(func=self.vim_send)

        copy_to_clipboard = subparsers.add_parser(
            "copy_to_clipboard", description="Copy string to clipboard"
        )
        copy_to_clipboard.add_argument(
            "string",
            nargs="+",
            help="A string to be evaluated and copied to clipboard",
            type=str,
        )
        copy_to_clipboard.set_defaults(func=self.copy_to_clipboard)

        edit = subparsers.add_parser("edit", aliases=["e"], description="Edit document")
        edit.set_defaults(func=self.edit)

        browse = subparsers.add_parser("browse", description="Browse document")
        browse.set_defaults(func=self.browse)

        rm = subparsers.add_parser("rm", description="Remove document")
        rm.add_argument("-s", "--selected", help="Force to delete only selected document even if some are marked.", action="store_true")
        rm.add_argument(
            "-o", "--option", help="Confirm deletion (1) or cancel (0)", type=int
        )
        rm.set_defaults(func=self.rm)

        reload = subparsers.add_parser("reload", description="Reload library")
        reload.set_defaults(func=self.reload)

        cmd = subparsers.add_parser("cmd", description="Put string on commandline")
        cmd.add_argument(
            "string", help="Provide a string to put on commandline", nargs="+", type=str
        )
        cmd.add_argument(
            "-f", "--search", help="Put into searchmode", action="store_true"
        )
        cmd.set_defaults(func=self.cmd)

        raise_helpwindow = subparsers.add_parser("help", description="Raise helpwindow")
        raise_helpwindow.set_defaults(func=self.raise_helpwindow)

        info_toggle = subparsers.add_parser(
            "info_toggle", description="Toggle infowindow"
        )
        info_toggle.set_defaults(func=self.info_toggle)

        info_cycle = subparsers.add_parser(
            "info_cycle", description="Cycle through views in infowindow"
        )
        info_cycle.set_defaults(func=self.info_cycle)

        info_scroll_down = subparsers.add_parser(
            "info_scroll_down", description="Scroll down in infowindow"
        )
        info_scroll_down.set_defaults(func=self.infowindow.scroll_down)

        info_scroll_up = subparsers.add_parser(
            "info_scroll_up", description="Scroll up in infowindow"
        )
        info_scroll_up.set_defaults(func=self.infowindow.scroll_up)

        self.commandparser = parser
