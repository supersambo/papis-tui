import curses
import locale
import os
import shlex

from wcwidth import wcwidth  # pip install wcwidth

locale.setlocale(locale.LC_ALL, "")  # Make sure Unicode works properly


class History:

    def __init__(self, config):
        self.list = {"command": [], "search": []}
        self.index = {"command": None, "search": None}
        self.file = {"command": None, "search": None}
        self.mode = "command"

        # init  history for search and command
        for mode in ["command", "search"]:
            try:
                path = config["commandline"]["history"][f"{mode}_file"]
                with open(path) as f:
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


class AutoCompleter:
    def __init__(self, config, commandparser):
        self.ghosts = []
        self.mode = "command"
        self.commandparser = commandparser
        self.list = {"command": [], "search": []}
        self.index = 0

        self.list["command"] += self.argparse_to_strings()

    @property
    def ghost(self):
        try:
            return self.ghosts[self.index]
        except IndexError:
            self.index = 0
            if len(self.ghosts) > 0:
                self.ghosts[self.index]
            else:
                return ""

    def next(self):
        if len(self.ghosts) - 1 > self.index:
            self.index += 1
        else:
            self.index = 0

    def argparse_to_strings(self, include_options=True, include_values=True):
        """
        Generate a flat list of possible commands and their options from argparse.

        :param include_options: if True, include option flags for each command
        :param include_values:  if True, append a trailing space to options
                                that expect a value
        :return: list of strings
        """
        parser = self.commandparser
        strings = []

        for action in parser._subparsers._group_actions:
            for cmd, subparser in action.choices.items():
                # base command
                strings.append(cmd)

                if include_options:
                    for opt_action in subparser._actions:
                        for opt in opt_action.option_strings:
                            if include_values and opt_action.nargs not in (0, None):
                                strings.append(f"{cmd} {opt} ")
                            else:
                                strings.append(f"{cmd} {opt}")

        return strings

    def get_completions(self, text, full=False):
        """
        Return possible completions based on the current token
        against self.completion_list.

        :param text: current input string
        :param full: if True, return full candidates (e.g. 'open -d')
                    if False, return only ghost suffix for current token
        :return: list of completions
        """
        if not text or text.isspace():
            self.ghosts = []
            return None

        tokens = shlex.split(text, posix=True)
        if text.endswith(" "):
            tokens.append("")

        last = tokens[-1]

        completions = []

        for candidate in self.list[self.mode]:
            cand_tokens = candidate.split()

            # Only consider candidates with at least as many tokens
            if len(tokens) > len(cand_tokens):
                continue

            # Prefix of candidate must match typed tokens (except last)
            if tokens[:-1] != cand_tokens[:len(tokens) - 1]:
                continue

            # Now compare last token against the corresponding candidate token
            cand_token = cand_tokens[len(tokens) - 1]
            if cand_token.startswith(last):
                if full:
                    completions.append(candidate)
                else:
                    completions.append(cand_token[len(last):])

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for c in completions:
            if c not in seen:
                seen.add(c)
                unique.append(c)
        self.ghosts = unique


class CommandPrompt:
    def __init__(self, stdscr, config, commandparser):
        self.stdscr = stdscr
        self.cursor_pos = 0
        y, x = self.stdscr.getmaxyx()
        self.win = curses.newwin(1, x, y - 1, 0)
        self.win.keypad(True)
        self.history = History(config)
        self.autocomp = AutoCompleter(config, commandparser)
        self._mode = None
        self.commandparser = commandparser
        self._size = {"posy": y-1, "posx": 0, "sizey": 1, "sizex": x}
        self.display_range = (None, None)
        self.cursor = {"display": 0, "input": 0}

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        self._mode = mode
        self.history.mode = mode
        self.autocomp.mode = mode
 
    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size):
        self._size = size
        self.win.mvwin(size["posy"], size["posx"])
        self.win.resize(size["sizey"], size["sizex"])
        # change input str here if text doesnt fit
        self.display()

    @property
    def display_chars(self):
        # if self.cursor_pos >= self.size["sizex"]-2 and self._display_width(self.input_chars) >= self.size["sizex"]-2:
        #     result = self.input_chars[-self.size["sizex"]+2:]
        # else:
        #     result = self.input_chars
        return self.input_chars[self.display_range[0]:self.display_range[1]]

    def display(self):
        self.win.erase()  # Clear only this line
        text = "".join(self.display_chars)
        self.autocomp.get_completions(text)
        line = f"{self.prompt}{text}"
        self.win.addstr(0, 0, line)
        if self.autocomp.ghost != "":
            self.win.addstr(0, len(self.display_chars) + 1,
                            self.autocomp.ghost, curses.A_DIM)
        cursor_x = len(self.prompt) + self._display_width(
            self.input_chars[: self.cursor["input"]]
        )
        if not cursor_x > self.size["sizex"]-1:
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
        self.cursor["input"] = self._display_width(self.input_chars)
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
                    if self.cursor > 0:
                        del self.input_chars[self.cursor["input"] - 1]
                        self.cursor["input"] -= 1
                elif ch == "\t":
                    self.autocomp.next()
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
                    self.input_chars.insert(self.cursor["input"], ch)
                    self.cursor["input"] += 1

            elif ch in (curses.KEY_BACKSPACE, 127):
                if self.cursor["input"] > 0:
                    del self.input_chars[self.cursor["input"] - 1]
                    self.cursor["input"] -= 1
            elif ch == curses.KEY_LEFT:
                if self.cursor["input"] > 0:
                    self.cursor["input"] -= 1
            elif ch == curses.KEY_RIGHT:
                if self.cursor["input"] < len(self.input_chars):
                    self.cursor["input"] += 1
                elif self.cursor["input"] == len(self.input_chars):
                    self.input_chars += list(self.autocomp.ghost)
                    self.cursor["input"] = len(self.input_chars)
            elif ch == curses.KEY_DC:
                if self.cursor["input"] < len(self.input_chars):
                    del self.input_chars[self.cursor["input"]]
            elif ch == curses.KEY_HOME:
                self.cursor["input"] = 0
            elif ch == curses.KEY_END:
                self.cursor["input"] = len(self.input_chars)
            elif ch == curses.KEY_UP:
                replacement = self.history.up()
                if replacement:
                    self.input_chars = replacement
                    self.cursor["input"] = len(self.input_chars)
            elif ch == curses.KEY_DOWN:
                replacement = self.history.down()
                if replacement is not None:
                    self.input_chars = replacement
                    self.cursor["input"] = len(self.input_chars)

            self.display()

        curses.curs_set(0)  # hide cursor again
        self.clear()
        return "".join(self.input_chars)
