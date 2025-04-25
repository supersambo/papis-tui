import curses
from papistui.helpers.styleparser import StyleParser


class CommandInfo:
    def __init__(self, stdscr):
        """Constructor method

        :param stdscr: curses stdscr (full screen)
        """

        self.styleparser = StyleParser()
        self.active = False
        self.pad = None
        self.size = {"sizey": 0, "sizex": 0, "posy": 0, "posx": 0}

    def destroy(self):
        """Destroy the command info window and update size and active vars"""
        if self.pad:
            self.pad.erase()
            self.pad.refresh(
                0,
                0,
                self.size["posy"],
                self.size["posx"],
                self.size["posy"] + self.size["sizey"],
                self.size["posx"] + self.size["sizex"] - 2,
            )
        self.size = {"sizey": 0, "sizex": 0, "posy": 0, "posx": 0}
        self.pad = None
        self.active = False

    def display(self, info):
        """
        Create pad and display information

        :param info: lines to be displayed
        :type info: list
        """

        self.active = True
        self.pad = curses.newpad(self.size["sizey"], self.size["sizex"])
        self.pad.erase()
        for idx, line in enumerate(info):
            self.styleparser.printline(
                screen=self.pad,
                string=line,
                posy=idx,
                xmax=self.size["sizex"] - 1,
                xoffset=0,
                align="left",
            )
            self.pad.refresh(
                0,
                0,
                self.size["posy"],
                self.size["posx"],
                self.size["posy"] + self.size["sizey"],
                self.size["posx"] + self.size["sizex"] - 2,
            )
