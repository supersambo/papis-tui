import curses
import locale

from wcwidth import wcwidth  # pip install wcwidth

locale.setlocale(locale.LC_ALL, "")  # Make sure Unicode works properly


class CommandPrompt:
    def __init__(self, stdscr, maxlen=100):
        self.stdscr = stdscr
        self.maxlen = maxlen
        self.cursor_pos = 0
        y, x = self.stdscr.getmaxyx()
        self.win = curses.newwin(1, x, y - 1, 0)

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

    def edit(self, prompt=":", prefill=""):
        self.input_chars = []
        self.prompt = prompt
        self.win.erase()
        self.input_chars = list(prefill)
        self.cursor_pos = len(self.input_chars)
        self.display()

        while True:
            ch = self.win.get_wch()

            if isinstance(ch, str):
                if ch == "\n":
                    break
                elif ch in ("\x08", "\x7f"):  # Backspace: BS or DEL
                    if self.cursor_pos > 0:
                        del self.input_chars[self.cursor_pos - 1]
                        self.cursor_pos -= 1
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
            elif ch == "\x1b":
                pass

            self.display()

        self.clear()
        return "".join(self.input_chars)
