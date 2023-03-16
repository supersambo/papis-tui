from papis.docmatcher import DocMatcher
from papis.database.cache import match_document
from papistui.helpers.styleparser import StyleParser
from papistui.features.sorting import sort_multiple_keys
import curses
import re


class DocumentList(object):
    def __init__(self, items, initsize, stdscr, config):
        """ Constructor method

        :param items: list of documents to be displayed
        :param initsize: dict containing initial size and position
        :param stdscr: curses stdscr (full screen)
        :param config: dict with configuration options
        """

        self.pad = None
        self.stdscr = stdscr
        self.config = config

        # style
        self.styleparser = StyleParser()
        self.style = self.config["documentlist"]["defaultstyle"]
        self.multilinestyle = self.config["documentlist"]["multilinestyle"]["rows"]
        self.mark = self.config["documentlist"]["marked-icon"]
        self.styleheight = len(self.multilinestyle)

        # items
        self._items = items
        self.view = items
        self.marked = []
        self.selected_doc = self.view[0]

        # positions and dimensions
        self._size = initsize
        self._top_idx = 0  # index of the first document in items idx_top_idx_itm
        self._selected_win_idx = 0  # position of selected option on window idx_sel_win
        self.selected_idx = 0  # index of selected_win_idx item in item list idx_sel_itm
        self.bottom = len(self.view)  # lenght of items in view
        self.rownr = self.getrownr()  # number of options that fit on window

        self.init_pad()
        self.sortkeys = self.config["documentlist"]["defaultsort"]
        if len(self.sortkeys) > 0:
            self.sort(self.sortkeys)

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size):
        """ Resize, reposition and display

        :param size: dict containing size and position
        """

        self._size = size
        self.pad.resize(self._size["sizey"], self.size["sizex"])
        self.rownr = self.getrownr()
        if self.selected_win_idx >= self.rownr:
            self.top_idx = self.selected_idx - self.rownr + 1
            self.selected_win_idx = self.rownr - 1
        self.display()

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, items):
        """ Set items sort (if sortkey present), set view and display

        :param items: list of documents
        """

        if self.sortkeys != "":
            self._items = sort_multiple_keys(items, self.sortkeys)
        else:
            self._items = items
        self.view = [item for item in self.items if item in self.view]
        self.bottom = len(self.view)
        self.display()

    @property
    def selected_win_idx(self):
        return self._selected_win_idx

    @selected_win_idx.setter
    def selected_win_idx(self, selected_win_idx):
        """ Set selected_win_idx and defer selected_idx and selected doc from it

        :param selected_win_idx: integer representing idx of selected item on screen
        """

        self._selected_win_idx = selected_win_idx
        self.selected_idx = self.top_idx + self._selected_win_idx
        self.selected_doc = self.view[self.selected_idx]

    @property
    def top_idx(self):
        return self._top_idx

    @top_idx.setter
    def top_idx(self, top_idx):
        """ Set top_idx and defer selected_idx and selected doc from it

        :param top_idx: integer representing idx of top item on screen among all items
        """
        self._top_idx = top_idx
        self.selected_idx = self._top_idx + self.selected_win_idx
        self.selected_doc = self.view[self.selected_idx]

    def init_pad(self):
        """ Setup the pad """
        self.pad = curses.newpad(self.size["sizey"], self.size["sizex"])
        self.pad.keypad(True)

    def marked_or_selected_docs(self):
        """ Return marked (if any) or selected (if none marked) document(s)

        :return list of document(s)
        """
        if len(self.marked) > 0:
            return self.marked
        else:
            return [self.selected_doc]

    def paging(self, direction):
        """ Scroll one page up or down

        :param direction: int -1 (up) or 1 (down)
        """

        pagenr = self.bottom // self.rownr
        selected_win_idx_page = (self.top_idx + self.selected_win_idx) // self.rownr
        next_page = selected_win_idx_page + direction
        # The last page may have fewer items than max lines,
        # so we should adjust the selected_win_idx cursor position as maximum item count on last page
        if next_page == pagenr:
            self.selected_win_idx = min(
                self.selected_win_idx, self.bottom % self.rownr - 1
            )

        # Page up
        # if selected_win_idx page is not a first page, page up is possible
        # top_idx position can not be negative, so if top_idx position is going to be negative, we should set it as 0
        if (direction == -1) and (selected_win_idx_page > 0):
            self.top_idx = max(0, self.top_idx - self.rownr)
            return
        # Page down
        # if selected_win_idx page is not a last page, page down is possible
        if (direction == 1) and (selected_win_idx_page < pagenr):
            self.top_idx += self.rownr
            return

    def scroll_down(self, *args):
        """ Scroll one document down if selected not last

        :return dict with exit status
        """

        # Down direction scroll overflow
        # next cursor position touchs the max lines, but absolute position of max lines could not touch the bottom
        if (
            self.selected_win_idx + 1 == self.rownr
            and self.top_idx + self.rownr < self.bottom
        ):
            self.top_idx += 1
            return
        # next cursor position is above max lines, and absolute position of next cursor could not touch the bottom
        if (
            self.selected_win_idx + 1 < self.rownr
            and self.top_idx + self.selected_win_idx + 1 < self.bottom
        ):
            self.selected_win_idx += 1
            return {"exit_status": 0}

    def scroll_up(self, *args):
        """ Scroll up one document down if selected not first

        :return dict with exit status
        """

        # Up direction scroll overflow
        # selected_win_idx cursor position is 0, but top_idx position is greater than 0
        if self.top_idx > 0 and self.selected_win_idx == 0:
            self.top_idx -= 1
            return
        # selected_win_idx cursor position or top_idx position is greater than 0
        if self.top_idx > 0 or self.selected_win_idx > 0:
            self.selected_win_idx -= 1
            return {"exit_status": 0}

    def page_up(self, *args):
        self.paging(-1)
        return {"exit_status": 0}

    def page_down(self, *args):
        self.paging(1)
        return {"exit_status": 0}

    def getrownr(self):
        """ Return number of documents that fit on one page

        :return int number of rows
        """

        curses.update_lines_cols()
        if self.style == "multiline":
            return int((self.size["sizey"] - 2) / (self.styleheight + 1))
        elif self.style == "table":
            return int(self.size["sizey"]) - 1

    def printtablerow(self, posy, doc=None, header=False, selected=False, marked=False):
        """ Print single row in table style

        :param posy: int vertical position where to print row
        :param doc: document to be displayed, defaults to None
        :param header: bool whether row is the header, defaults to False
        :param selected: bool whether current row the selected, defaults to False
        :param marked: boll whether document is in marked, defaults to False
        """
        sep = self.config["documentlist"]["tablestyle"]["separator"]
        if header:
            style = self.config["documentlist"]["tablestyle"]["headerstyle"]
        else:
            style = (
                self.config["documentlist"]["tablestyle"]["cursorrowstyle"]
                if selected
                else self.config["documentlist"]["tablestyle"]["rowstyle"]
            )
        string = self.mark if marked else " "
        xoffset = 2
        self.styleparser.sprintline(
            screen=self.pad,
            string=string,
            posy=posy,
            xmax=xoffset,
            xoffset=0,
            style=style,
            fill=True,
        )

        columns = self.config["documentlist"]["tablestyle"]["columns"]
        for idx, column in enumerate(columns):
            string = column["header"] if header else column["content"]
            # content
            if xoffset < self.size["sizex"]:
                xmax = (
                    column["width"]
                    if xoffset + column["width"] < self.size["sizex"]
                    else self.size["sizex"] - xoffset - 1
                )
                self.styleparser.sprintline(
                    screen=self.pad,
                    string=string,
                    posy=posy,
                    xmax=xmax,
                    xoffset=xoffset,
                    style=style,
                    doc=doc,
                    fill=True,
                )
                xoffset += column["width"]
            # separator
            if xoffset < self.size["sizex"] and idx < len(columns) - 1:
                xmax = (
                    len(sep)
                    if xoffset + len(sep) < self.size["sizex"]
                    else self.size["sizex"] - xoffset - 1
                )
                self.styleparser.sprintline(
                    screen=self.pad,
                    string=sep,
                    posy=posy,
                    xmax=xmax,
                    xoffset=xoffset,
                    style=style,
                    doc=doc,
                    fill=True,
                )
                xoffset += len(sep)

    def display(self):
        """ Display documents on window """

        self.pad.erase()
        if self.style == "table":
            self.printtablerow(header=True, posy=0)
            for idx, item in enumerate(
                self.view[self.top_idx : self.top_idx + self.rownr]
            ):
                self.printtablerow(
                    posy=idx + 1,
                    doc=item,
                    header=False,
                    marked=item in self.marked,
                    selected=idx == self.selected_win_idx,
                )

        elif self.style == "multiline":
            frametop_idx = "╭" + "─" * int(self.size["sizex"] - 2) + "╮"
            framebottom = "╰" + "─" * int(self.size["sizex"] - 2) + "╯"
            itemstart = lambda idx: idx * (self.styleheight + 1) + 1
            # draw items
            for idx, item in enumerate(
                self.view[self.top_idx : self.top_idx + self.rownr]
            ):
                for linenr, line in enumerate(self.multilinestyle):
                    self.styleparser.printline(
                        screen=self.pad,
                        string=line,
                        posy=itemstart(idx) + linenr,
                        xmax=self.size["sizex"] - 1,
                        doc=item,
                        xoffset=3,
                        align="left",
                    )

                if item in self.marked:
                    self.pad.addstr(itemstart(idx), 1, self.mark, 7)
            # draw frame
            self.pad.addstr(itemstart(self.selected_win_idx) - 1, 0, frametop_idx, 7)
            self.pad.addstr(
                itemstart(self.selected_win_idx) + self.styleheight, 0, framebottom, 7
            )
            for i in range(0, self.styleheight):
                self.pad.addstr(itemstart(self.selected_win_idx) + i, 0, "│", 7)
                self.pad.addstr(
                    itemstart(self.selected_win_idx) + i, self.size["sizex"] - 1, "│", 7
                )

        self.pad.refresh(
            0,
            0,
            self.size["posy"],
            self.size["posx"],
            self.size["sizey"],
            self.size["sizex"] - 1,
        )

    def refresh(self):
        """ Refresh underlying pad """

        self.pad.refresh(
            0,
            0,
            self.size["posy"],
            self.size["posx"],
            self.size["sizey"],
            self.size["sizex"] - 1,
        )

    def jump_to_top(self, *args):
        """ Select first document in view """

        self.top_idx = 0
        self.selected_win_idx = 0

        return {"exit_status": 0}

    def jump_to_bottom(self, *args):
        """ Select last document in view """

        if len(self.view) >= self.rownr:
            self.top_idx = len(self.view) - self.rownr
            self.selected_win_idx = self.rownr - 1
        else:
            self.top_idx = 0
            self.selected_win_idx = len(self.view) - 1

        return {"exit_status": 0}

    def togglestyle(self, *args):
        """ Switch between multiline and table document presentation """

        if self.style == "multiline":
            self.style = "table"
            self.rownr = self.getrownr()
        else:
            self.style = "multiline"
            self.rownr = self.getrownr()
            if self.selected_win_idx >= self.rownr:
                self.top_idx = self.selected_idx
                self.selected_win_idx = 0

        return {"exit_status": 0}

    def mark_selected(self, *args):
        """ Toggle mark on selected document """

        if self.view[self.selected_idx] in self.marked:
            self.marked.remove(self.view[self.selected_idx])
        else:
            self.marked.append(self.view[self.selected_idx])

        return {"exit_status": 0}

    def mark_view(self, *args):
        """ Mark all documents in current view """

        for i in self.view:
            if i not in self.marked:
                self.marked.append(i)

        return {"exit_status": 0}

    def unmark_all(self, *args):
        """ Remove all documents from list of marked

        :return dictionary with exit status
        """
        self.marked = []
        return {"exit_status": 0}

    def mark_down(self, *args):
        """ Mark selected document and scroll down

        :return dictionary with exit status
        """

        self.mark_selected()
        self.scroll_down()
        return {"exit_status": 0}

    def view_reset(self, *args):
        """ Reset view to see all documents """

        self.view = self.items
        self.bottom = len(self.items)
        return {"exit_status": 0}

    def view_marked(self, *args):
        """ Set view to only those documents currently marked """

        marked = [item for item in self.view if item in self.marked]
        if len(marked) > 0:
            self.view = marked
            self.selected_win_idx = 0
            self.top_idx = 0
            self.bottom = len(self.view)
            return {"exit_status": 0}
        else:
            return {"exit_status": 2, "message": ("No documents marked", "error")}

    def getinfo(self):
        """ Return information about the current context
        Ultimately passed to statusbar

        :return dict with context information

        """

        return {
            "idx": str(self.selected_idx + 1),
            "selected_win_idx": str(self.selected_win_idx + 1),
            "marked": str(len(self.marked)),
            "view": str(len(self.view)),
            "items": str(len(self.items)),
            "sortkeys": " ".join(self.sortkeys),
        }

    def docmatch(self, query):
        """ Filter documents based on query

        :param query: str query to be interpreted by papis docmatch
        """
        try:
            aliases = self.config["commandline"]["search"]["keyword_aliases"]
            for alias in aliases:
                regex = r"\b" + re.escape(alias) + r"\b"
                query = re.sub(regex, aliases[alias], query)
        except:
            pass

        DocMatcher.set_matcher(match_document)
        DocMatcher.parse(query)
        self.results = []
        for item in self.items:
            if DocMatcher.return_if_match(item) is not None:
                self.results.append(item)
        if len(self.results) > 0:
            self.selected_win_idx = 0
            self.view = self.results
            self.bottom = len(self.view)
            self.top_idx = 0
            self.display()
            return {"exit_status": 0}
        else:
            return {
                "exit_status": 2,
                "message": ("No matching documents found", "error"),
            }

    def sort(self, sortkeys):
        """ Set sort string and reset view

        :param sortkeys: list of keys. Trailing '-' will sort decreasing
        """
        self.sortkeys = sortkeys
        self.items = self.items
        self.jump_to_top()
        return {"exit_status": 0}
