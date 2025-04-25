import argparse
import re

from papistui.helpers.styleparser import StyleParser


class HelpWindow:
    def __init__(self, stdscr, keymappings, commandparser, docpad):
        """Constructor method

        :param stdscr: curses stdscr for whole terminal
        :param keymappings: keymappings of class KeyMappings
        :param commandparser: argparse argument parser where command are defined
        :param docpad: the documentlist curses pad
        """
        self.active = False
        self.styleparser = StyleParser()
        self.keymappings = keymappings
        self.commandparser = commandparser
        self.subparsers = [
            subparser
            for action in self.commandparser._actions
            if isinstance(action, argparse._SubParsersAction)
            for _, subparser in action.choices.items()
        ]
        self.docpad = docpad
        self.linenr = None
        self.win = None
        self.stdscr = stdscr
        self.keychain = None
        self.sizey = 0
        self.sizex = 0
        self._yoffset = 0

    @property
    def yoffset(self):
        return self._yoffset

    @yoffset.setter
    def yoffset(self, yoffset):
        """Sets vertical scroll position and displays help

        :param yoffset: integer that defines from which line forward cont is displayed
        """

        self._yoffset = yoffset
        self.display()

    def jump_to_top(self):
        self.yoffset = 0

    def jump_to_bottom(self):
        self.yoffset = self.linenr - self.sizey + 2

    def scroll_down(self):
        if not self.yoffset >= self.linenr - self.sizey + 2:
            self.yoffset = self._yoffset + 1

    def scroll_up(self):
        if not self.yoffset <= 0:
            self.yoffset = self._yoffset - 1

    def build_help(self, rows, cols):
        """Create content for help lines

        :param rows: number of rows
        :param cols: number of columns
        """
        m = int(self.sizex / 2) - 3
        lines = []
        lines.append(("<bold>Help</bold>", "center", True))
        lines.append(("", "left", True))
        lines.append(("<underline>Keymappings</underline>", "center", True))
        lines.append(("", "left", True))
        for key, value in self.keymappings.items():
            lines.append((f"{key.rjust(m)} :: {value}", "left", False))

        lines.append(("", "left", True))
        lines.append(("<underline>Available commands</underline>", "center", True))
        lines.append(("", "left", True))
        for subparser in self.subparsers:
            cmd = re.sub(r"^.*\s", "", subparser.prog)
            lines.append(
                (f"{cmd.rjust(m)} :: {subparser.description}", "left", False)
            )

        lines.append(("", "left", True))
        self.linenr = len(lines)

        return lines

    def display(self):
        """Display Helpwindow"""

        self.active = True
        rows, cols = self.stdscr.getmaxyx()
        self.sizex = cols - 2
        self.sizey = rows - 2
        self.stdscr.erase()
        # self.stdscr.clear()
        content = self.build_help(rows, cols)
        for idx, line in enumerate(
            content[self.yoffset : self.sizey + self.yoffset - 1]
        ):
            self.styleparser.printline(
                screen=self.stdscr,
                string=line[0],
                posy=idx + 1,
                xmax=self.sizex,
                xoffset=1,
                align=line[1],
                evaluate=False,
                parse=line[2],
            )

        self.stdscr.refresh()
