import curses
import re
from papistui.helpers.styleparser import StyleParser


class KeyInfo(object):
    def __init__(self, stdscr):
        """ Constructor method

        :param stdscr: curses stdscr object (full screen)
        """
        self.styleparser = StyleParser()
        self.win = None
        self.stdscr = stdscr
        self.keychain = None
        self.sizey = 0
        self.sizex = 0

    def format_rows(self, options):
        """ Formats and aligns the available options

        :param options: list of available options
        """

        self.sizey = len(options) + 1
        self.sizex = max([(len(i["km"]) + len(i["cmd_desc"])) for i in options]) + 7
        rows = []
        for option in options:
            length = len(option["km"]) + len(option["cmd_desc"]) + 4
            p1 = "{}{}".format(" " * (self.sizex - length), option["keys_typed"])
            p2 = "{} :: {} ".format(option["keys_opt"], option["cmd_desc"])
            row = (p1, p2)
            rows.append(row)

        return rows

    def display(self, doclist, options):
        """ Display keyhints on top of documentlist pad in bottom right corner

        :param doclist: The Documentlist objects which includes screen
        :param options: list of options to be displayed
        """
        lines = self.format_rows(options)
        posy = doclist.size["sizey"] - self.sizey
        posx = doclist.size["sizex"] - self.sizex - 1
        self.win = curses.newwin(self.sizey, self.sizex, posy, posx)
        for idx, line in enumerate(lines):
            self.styleparser.sprintline(
                screen=self.win,
                string=line[0],
                posy=idx,
                xmax=self.sizex,
                xoffset=0,
                style="dim",
            )
            self.styleparser.sprintline(
                screen=self.win,
                string=line[1],
                posy=idx,
                xmax=self.sizex,
                xoffset=len(line[0]),
                style="",
            )

        self.win.overlay(doclist.pad)
        self.win.refresh()
