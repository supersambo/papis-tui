import curses
from papistui.helpers.styleparser import StyleParser


class StatusBar:
    def __init__(self, initsize, stdscr, config):
        """Constructor method

        :param initsize: dict with initial size and position
        :param stdscr: curses stdscr (full screen)
        :param config: dict configuration options
        """
        self._size = initsize
        self._info = {"idx": 0, "view": 0, "selected": 0, "items": 0}
        self.pad = curses.newpad(initsize["sizey"], initsize["sizex"])
        self.styleparser = StyleParser()
        self.mode = "normal"
        self.config = config

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size):
        """Resize, reposition and display

        :param size: dict containing size and position
        """

        self._size = size
        self.pad.resize(self._size["sizey"], self.size["sizex"])
        self.display()

    @property
    def info(self):
        return self._info

    @info.setter
    def info(self, info):
        self._info = info
        self.display()

    def display(self):
        """Format statusbar info based on mode and display"""

        self.pad.erase()
        left, right = ("", "")
        if self.mode in self.config["statusbar"]["left"]:
            left = self.config["statusbar"]["left"][self.mode]
        else:
            left = self.config["statusbar"]["left"]["default"]

        if self.mode in self.config["statusbar"]["right"]:
            right = self.config["statusbar"]["right"][self.mode]
        else:
            right = self.config["statusbar"]["right"]["default"]

        self.info.update({"mode": self.mode, "mode_upper": self.mode.upper()})
        self.styleparser.printline(
            screen=self.pad,
            string=left,
            additional=self.info,
            posy=0,
            xmax=self.size["sizex"] - 1,
            xoffset=0,
            align="left",
        )
        self.styleparser.printline(
            screen=self.pad,
            string=right,
            additional=self.info,
            posy=0,
            xmax=self.size["sizex"] - 1,
            xoffset=0,
            align="right",
        )
        self.pad.refresh(
            0,
            0,
            self.size["posy"],
            self.size["posx"],
            self.size["posy"] + self.size["sizey"],
            self.size["posx"] + self.size["sizex"] - 1,
        )
