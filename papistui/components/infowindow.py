import curses
from itertools import cycle
from papistui.helpers.styleparser import StyleParser


class InfoWindow:
    def __init__(self, stdscr, config):
        """Constructur method

        :param stdscr: curses stdscr (full screen)
        :param config: configuration dictionary
        """

        self.styleparser = StyleParser()
        self.config = config
        self.active = False
        self.pad = None
        self._size = {"sizey": 0, "sizex": 0, "posy": 0, "posx": 0}
        self._yscroll = 0

        try:
            # check if config file has views section
            self.views = self.config["infowindow"]["views"]
            self.enabled = True
        except KeyError:
            self.enabled = False

        if self.enabled:
            self.viewnames = list(self.views)
            self.iterview = cycle(self.views)
            self.view = next(self.iterview)
            for view in self.views:
                self.views[view].setdefault("content", "")
                self.views[view].setdefault("height", 3)
                self.views[view].setdefault("linewrap", True)
                self.views[view].setdefault("align", "left")

    @property
    def yscroll(self):
        return self._yscroll

    @yscroll.setter
    def yscroll(self, yscroll):
        """Set scroll position and display

        :param yscroll: integer presenting idx from which to start
        """
        self._yscroll = yscroll
        if self.active:
            self.display()

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size):
        self._size = size
        if self.active:
            self.display()

    def activate(self, view=None):
        """Calculate size and activate window

        :param view: name of view to be displayed, defaults to None
        """
        self.size = {"sizey": self.views[self.view]["height"] + 2}
        self.active = True

    def deactivate(self):
        self.active = False
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

    def scroll_down(self, *args):
        self.yscroll = self.yscroll + 1

    def scroll_up(self, *args):
        if self.yscroll > 0:
            self.yscroll = self.yscroll - 1

    def next_view(self):
        self.active = True
        self.view = next(self.iterview)
        self._size = {"sizey": self.views[self.view]["height"] + 2}

    def draw_border(self):
        # top
        frametop = (
            "╭"
            + "─"
            + " "
            + self.view
            + " "
            + "─" * int(self.size["sizex"] - len(self.view) - 6)
            + "╮"
        )
        self.styleparser.printline(
            screen=self.pad,
            string=frametop,
            posy=0,
            xmax=self.size["sizex"],
            xoffset=0,
            align="left",
        )
        # bottom
        framebottom = "╰" + "─" * int(self.size["sizex"] - 3) + "╯"
        self.styleparser.printline(
            screen=self.pad,
            string=framebottom,
            posy=self.size["sizey"] - 1,
            xmax=self.size["sizex"],
            xoffset=0,
            align="left",
        )
        # sides
        for i in range(1, self.size["sizey"] - 1):
            # left
            self.pad.addstr(i, 0, "│", 7)
            # right
            self.pad.addstr(i, self.size["sizex"] - 2, "│", 7)

    def display(self):
        self.active = True
        self.pad = curses.newpad(self.size["sizey"], self.size["sizex"])
        self.pad.erase()
        info = self.views[self.view]["content"]
        doc = self.doclist.selected_doc
        x = self.styleparser.printline(
            screen=self.pad,
            string=info,
            posy=1,
            xmax=self.size["sizex"] - 4,
            ymax=self.views[self.view]["height"],
            yscroll=self.yscroll,
            xoffset=2,
            align="left",
            doc=doc,
            wraplines=self.views[self.view]["linewrap"],
            evaluate=True,
        )
        self._yscroll = x["yscroll"]
        self.draw_border()
        self.pad.refresh(
            0,
            0,
            self.size["posy"],
            self.size["posx"],
            self.size["posy"] + self.size["sizey"],
            self.size["posx"] + self.size["sizex"] - 2,
        )
