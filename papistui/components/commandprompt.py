import curses
import locale
import os

from wcwidth import wcwidth  # pip install wcwidth

locale.setlocale(locale.LC_ALL, "")  # Make sure Unicode works properly

class History:
    def __init__(self, config):
        self.list = {"command": [], "search": []}
        self.index = {"command": None, "search": None}
        self.file = {"command": None, "search": None}
        self.mode = "command"

        #init  history for search and command
        for mode in ["command", "search"]:
            try:
                path = config["commandline"]["history"][f"{mode}_file"]
                with open(path, "r") as f:
                    self.list[mode] = [line.strip() for line in f if line.strip()]
                self.file[mode] = path
            except FileNotFoundError:
                # create an empty file
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f:
                    pass
                self.list[mode] = []
                self.file[mode] = path
            except Exception:
                self.list[mode] = []

    def reset_indices(self):
        self.index = {"command": None, "search": None}

    def up(self):
        if self.list[self.mode]:
            if self.index[self.mode] is None:
                self.index[self.mode] = len(self.list[self.mode]) - 1
            elif self.index[self.mode] > 0:
                self.index[self.mode] -= 1
            return list(self.list[self.mode][self.index[self.mode]])

    def down(self):
        if self.list[self.mode] and self.index[self.mode] is not None:
            if self.index[self.mode] < len(self.list[self.mode]) - 1:
                self.index[self.mode] += 1
                return list(self.list[self.mode][self.index[self.mode]])
            else:
                self.index[self.mode] = None
                return []

    def save(self, command, mode):
        if not command or mode not in ["command", "search"]:
            return
        if len(self.list[mode]) > 0 and command == self.list[mode][-1]:
            return
        self.list[mode].append(command)
        if self.file[mode]:
            with open(self.file[mode], "a") as f:
                f.write(command + "\n")


class CommandPrompt:
    def __init__(self, stdscr, config, maxlen=100):
        self.stdscr = stdscr
        self.maxlen = maxlen
        self.cursor_pos = 0
        y, x = self.stdscr.getmaxyx()
        self.win = curses.newwin(1, x, y - 1, 0)
        self.win.keypad(True)
        self.history = History(config)
        self._mode = None

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        self._mode = mode
        self.history.mode = mode


    def display(self):
        self.win.erase()  # Clear only this line
        line = f"{self.prompt}{''.join(self.input_chars)}"
        self.win.addstr(0, 0, line)
        cursor_x = len(self.prompt) + self._display_width(
            self.input_chars[: self.cursor_pos]
        )
        self.win.move(0, cursor_x)
        self.win.refresh()

    def clear(self):
        self.win.erase()
        self.win.refresh()

    def _display_width(self, chars):
        return sum(max(wcwidth(c), 0) for c in chars)

    def edit(self, mode, prefill=""):
        self.mode = mode
        self.history.reset_indices()
        self.input_chars = list(prefill)
        if mode in ["command", "select"]:
            self.prompt = ":"
        elif mode == "search":
            self.prompt = "/"
        else:
            self.prompt = ""
        self.cursor_pos = len(self.input_chars)
        self.win.erase()
        self.win.keypad(True)         # make arrow keys work
        curses.curs_set(1)            # show cursor while editing
        self.display()

        while True:
            ch = self.win.get_wch()

            if isinstance(ch, str):
                if ch == "\n":  # Enter
                    command = "".join(self.input_chars).strip()
                    self.history.save(command, self.mode)
                    break
                elif ch in ("\x08", "\x7f"):  # Backspace: BS or DEL
                    if self.cursor_pos > 0:
                        del self.input_chars[self.cursor_pos - 1]
                        self.cursor_pos -= 1
                elif ch == "\x1b":  # ESC pressed
                    # check if it's really ESC alone (cancel)
                    self.win.nodelay(True)
                    try:
                        nxt = self.win.get_wch()
                    except curses.error:
                        nxt = None
                    self.win.nodelay(False)

                    if nxt is None:
                        self.input_chars = []
                        break
                    else:
                        # put it back for curses to interpret
                        curses.unget_wch(nxt)
                else:
                    if len(self.input_chars) < self.maxlen:
                        self.input_chars.insert(self.cursor_pos, ch)
                        self.cursor_pos += 1

            elif ch in (curses.KEY_BACKSPACE, 127):
                if self.cursor_pos > 0:
                    del self.input_chars[self.cursor_pos - 1]
                    self.cursor_pos -= 1
            elif ch == curses.KEY_LEFT:
                if self.cursor_pos > 0:
                    self.cursor_pos -= 1
            elif ch == curses.KEY_RIGHT:
                if self.cursor_pos < len(self.input_chars):
                    self.cursor_pos += 1
            elif ch == curses.KEY_DC:
                if self.cursor_pos < len(self.input_chars):
                    del self.input_chars[self.cursor_pos]
            elif ch == curses.KEY_HOME:
                self.cursor_pos = 0
            elif ch == curses.KEY_END:
                self.cursor_pos = len(self.input_chars)
            elif ch == curses.KEY_UP:
                replacement = self.history.up()
                if replacement:
                    self.input_chars = replacement
                    self.cursor_pos = len(self.input_chars)
            elif ch == curses.KEY_DOWN:
                replacement = self.history.down()
                if replacement is not None:
                    self.input_chars = replacement
                    self.cursor_pos = len(self.input_chars)

            self.display()

        curses.curs_set(0)  # hide cursor again
        self.clear()
        return "".join(self.input_chars)
