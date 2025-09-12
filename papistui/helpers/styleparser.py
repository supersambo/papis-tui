import curses
from html.parser import HTMLParser
from itertools import product


class StyleParser(HTMLParser):
    def __init__(self):
        """ Constructor method """
        HTMLParser.__init__(self)
        self.fmt = []
        self.output = []
        self.styledict = {}
        self.create_style_dict()

    def create_style_dict(self):
        """ Create a dictionary of styles and their numeric representation """

        colornames = {
            "bg": -1,
            "black": 0,
            "red": 1,
            "green": 2,
            "yellow": 3,
            "blue": 4,
            "magenta": 5,
            "cyan": 6,
            "white": 7,
        }
        colorcombs = [
            cmb for cmb in product(colornames.keys(), repeat=2) if cmb[0] != cmb[1]
        ]

        for i, cmb in enumerate(colorcombs):
            if __name__ != "__main__":
                curses.init_pair(i, colornames[cmb[0]], colornames[cmb[1]])
                self.styledict.update(
                    {f"{cmb[0]}_{cmb[1]}": curses.color_pair(i)}
                )
            else:
                self.styledict.update({f"{cmb[0]}_{cmb[1]}": 0})

        styledict = {
            "altcharset": curses.A_ALTCHARSET,
            "blink": curses.A_BLINK,
            "bold": curses.A_BOLD,
            "dim": curses.A_DIM,
            "invis": curses.A_INVIS,
            "italic": curses.A_ITALIC,
            "em": curses.A_ITALIC,
            "normal": curses.A_NORMAL,
            "protect": curses.A_PROTECT,
            "reverse": curses.A_REVERSE,
            "standout": curses.A_STANDOUT,
            "underline": curses.A_UNDERLINE,
            "horizontal": curses.A_HORIZONTAL,
            "left": curses.A_LEFT,
            "right": curses.A_RIGHT,
            "top": curses.A_TOP,
            "vertical": curses.A_VERTICAL,
            "chartext": curses.A_CHARTEXT,
            "black": self.styledict["black_bg"],
            "red": self.styledict["red_bg"],
            "green": self.styledict["green_bg"],
            "yellow": self.styledict["yellow_bg"],
            "blue": self.styledict["blue_bg"],
            "magenta": self.styledict["magenta_bg"],
            "cyan": self.styledict["cyan_bg"],
            "white": self.styledict["white_bg"],
            "ansiblack": self.styledict["black_bg"],
            "ansired": self.styledict["red_bg"],
            "ansigreen": self.styledict["green_bg"],
            "ansiyellow": self.styledict["yellow_bg"],
            "ansiblue": self.styledict["blue_bg"],
            "ansimagenta": self.styledict["magenta_bg"],
            "ansicyan": self.styledict["cyan_bg"],
            "ansiwhite": self.styledict["white_bg"],
        }

        self.styledict = {**self.styledict, **styledict}

    def compute_style(self, styles):
        """ Return the numeric representation of a (combination of) styles

        :param styles: str of styles separated by pipe e.g. bold|red
        :return int representation of style
        """
        styles = styles.split("|")
        styles = [style for style in styles if style != ""]
        styles = [style for style in styles if style in self.styledict.keys()]
        if len(styles) > 0:
            style = 0
            for i in styles:
                style = style | self.styledict[i]
        else:
            style = curses.A_NORMAL

        return style

    def handle_starttag(self, tag, attrs):
        self.fmt.append(tag)

    def handle_data(self, data):
        self.output.append({"format": "|".join(self.fmt), "content": data})

    def handle_endtag(self, tag):
        self.fmt.remove(tag)

    def parse(self, string, doc=None, additional=None, evaluate=True):
        """ Parse a string containing style tags and elements to be evaluated

        :param string: str to be parsed
        :param doc: document for which information should be parsed, defaults to None
        :param additional: additional objects to be made available for evaluation,
            defaults to None
        :param evaluate: bool whether to evaluate or only parse, defaults to True
        :return list of dict containing parsing results to be printed
        """
        self.fmt = []
        self.output = []
        if evaluate:
            string = self.evaluate(string, doc=doc, info=additional)
        try:
            self.feed(string)
        except:
            result = [{
                "content": string,
                "style": 0,
                "posx": 0,
                "len": len(string),
                }]
            return result

        result = []
        posx = 0
        for i in self.output:
            result.append(
                {
                    "content": i["content"],
                    "style": self.compute_style(i["format"]),
                    "posx": posx,
                    "len": len(i["content"]),
                }
            )
            posx = posx + len(i["content"])

        return result

    def nonparse(self, string):
        """
        Return a list containing dict in the format returned by parse without parsing

        :param string: str to be used
        :return list of dict
        """
        result = [{"content": string, "style": 0, "posx": 0, "len": len(string)}]
        return result

    def wraplines(self, printjobs, xmax):
        """ Convert parsing output into line wrapped output

        :param printjobs: list of dicts as returned by parse
        :param xmax: int length of line (where to put linebreak)
        """

        i = 0
        posx = 0
        printjob = printjobs[i]
        content = printjob["content"]
        result = []
        row = []
        while i < len(printjobs):
            if posx + len(content) <= xmax:
                row.append(
                    {
                        "content": content,
                        "style": printjob["style"],
                        "posx": posx,
                        "len": len(content),
                    }
                )
                posx = posx + len(content)
                i += 1
                if i == len(printjobs):  # if last
                    result.append(row)
                    pass
                else:
                    printjob = printjobs[i]
                    content = printjob["content"]
            else:
                space = xmax - posx
                txt = content[:space]
                content = content[space:]
                row.append(
                    {
                        "content": txt,
                        "posx": posx,
                        "len": space,
                        "style": printjob["style"],
                    }
                )
                result.append(row)
                row = []
                posx = 0

        return result

    def printline(
        self,
        screen,
        string,
        posy,
        xmax,
        ymax=1,
        yscroll=None,
        doc=None,
        additional=None,
        xoffset=0,
        align="left",
        evaluate=True,
        parse=True,
        wraplines=False,
    ):
        """ Main function parses evaluates and prints string on screen

        :param screen: curses win or pad where on which to print
        :param string: str to be parsed evaluated and printed
        :param posy: int vertical position indicating where to print
        :param xmax: int maximum space available in x direction
        :param ymax: int maximum space available in y direction, defaults to 1
        :param yscroll: int scroll position whene wraplines True, defaults to None
        :param doc: document used for string evaluation, defaults to None
        :param additional: additional variable to be used for string evaluation,
            defaults to None
        :param xoffset: int for shifting start to the right, defaults to 0
        :param align: str text alignment either "left", "right" or "center",
            defaults to "left"
        :param evaluate: bool whether to evaluate strings within {}, defaults to True
        :param parse: bool whether to parse string, defaults to True
        :param wraplines: bool whether to break lines on xmax, defaults to False
        """

        if type(string) is not list:
            strings = [string]
        else:
            strings = string

        lines = []

        for string in strings:
            if parse:
                printjobs = self.parse(string, doc, additional, evaluate=evaluate)
            else:
                printjobs = self.nonparse(string)
            if wraplines and len(printjobs) > 0:
                result = self.wraplines(printjobs, xmax=xmax - 2)
                for line in result:
                    lines.append(line)
            else:
                lines.append(printjobs)

        if ymax >= len(lines):
            yscroll = 0
        if not yscroll:
            yscroll = 0
        elif yscroll + ymax > len(lines):
            yscroll = yscroll - 1

        for idx, printjobs in enumerate(lines[yscroll : yscroll + ymax]):
            flen = 0
            for i in printjobs:
                flen = flen + i["len"]
            for p in printjobs:
                end = xoffset + p["posx"] + p["len"]
                cutoff = None if end <= xmax else xmax - end
                if align == "right":
                    startx = xmax - flen
                    startx = 0 if startx < 0 else startx

                elif align == "center":
                    startx = int(xmax / 2 - flen / 2)
                    startx = 0 if startx < 0 else startx

                else:
                    startx = xoffset

                screen.addstr(
                    posy + idx, startx + p["posx"], p["content"][:cutoff], p["style"]
                )

                if xoffset + p["posx"] + p["len"] >= xmax:
                    break
        return {"yscroll": yscroll}

    def sprintline(
        self,
        screen,
        string,
        style,
        posy,
        xmax,
        xoffset=0,
        fill=False,
        doc=None,
        additional=None,
    ):
        """ Simpler version of the printline method
        Does not allow in-text styling but accepts on style
        for the whole string to be printed

        :param screen: curses win or pad where on which to print
        :param string: str to be evaluated and printed
        :param style: str style for entire print e.g "bold|red"
        :param posy: int vertical position indicating where to print
        :param xmax: int maximum space available in x direction
        :param xoffset: int for shifting start to the right, defaults to 0
        :param fill: Whether to fill all empty space with white spaces
        this is used for linewise highlighting, defaults to False
        :param doc: document used for string evaluation, defaults to None
        :param additional: additional variable to be used for string evaluation,
            defaults to None
        """
        string = self.evaluate(string, doc=doc, info=additional)
        if fill:
            filler = xmax - len(string)
            string = string + filler * " "

        style = self.compute_style(style)
        screen.addstr(posy, xoffset, string[:xmax], style)

    def parse_braces(self, string):
        """ Extract parts from strings within curly braces to be evaluated

        :param string: str to be parsed
        :returns list of dictionary with extracted string and boolean indicating
        whether it is to be evaluated
        """
        opening = 0
        result = []
        istring = ""
        for idx, i in enumerate(string):
            if i == "{" and string[idx - 1] != "\\":
                if opening == 0:
                    result.append({"eval": False, "string": istring})
                    istring = ""
                else:
                    istring += i
                opening += 1
            elif i == "}" and string[idx - 1] != "\\":
                opening -= 1
                if opening == 0:
                    result.append({"eval": True, "string": istring})
                    istring = ""
                else:
                    istring += i
            else:
                if i == "\\" and string[idx + 1] in ["{", "}"]:
                    pass
                else:
                    istring += i

        if istring != "":
            result.append({"eval": False, "string": istring})
        return result

    def evaluate(self, strings, doc=None, docs=None, info=None):
        """ Evaluate content in curly braces

        :param strings: str to be evaluated
        :param doc: document to be available for evaluation, defaults to None
        :param info: dict context info available for evaluation, defaults to None
        """

        result = ""
        strings = self.parse_braces(strings)
        for string in strings:
            if string["eval"]:
                try:
                    result += eval(string["string"])
                except Exception:
                    result += "evalerr"
            else:
                result += string["string"]
        return result
