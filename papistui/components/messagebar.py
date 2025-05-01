import curses

from papistui.helpers.styleparser import StyleParser


class MessageBar:
    def __init__(self, stdscr):
        """Constructor method

        :param stdscr: curses stdscr (full screen)
        """
        self.styleparser = StyleParser()
        self.styles = {"error": "red", "success": "green", "neutral": "white"}
        self.active = False
        self.pad = None
        self.size = {"sizey": 0, "sizex": 0, "posy": 0, "posx": 0}
        self.active = False

    def destroy(self):
        """Clean pad and set to inactive. Space remains reserved"""

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

    def display(self, message):
        """Display error, success or neutral message

        :param message: either str or tuple in the form of (message, message_type)
                        where message_type is either 'success', 'neutral', 'error'
        """

        if type(message) is tuple:
            message_type = message[1]
            message = message[0]
        else:
            message = str(message)
            message_type = "neutral"

        self.active = True
        self.pad = curses.newpad(self.size["sizey"], self.size["sizex"])
        self.pad.erase()
        self.styleparser.sprintline(
            screen=self.pad,
            string=message,
            style=self.styles[message_type],
            posy=0,
            xmax=self.size["sizex"] - 1,
            xoffset=0,
            fill=True,
        )
        self.pad.refresh(
            0,
            0,
            self.size["posy"],
            self.size["posx"],
            self.size["posy"] + self.size["sizey"],
            self.size["posx"] + self.size["sizex"] - 2,
        )
