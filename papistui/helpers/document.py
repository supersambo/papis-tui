"""
This is used to inject additional methods into papis Document class
"""

from papis import api
from papis.document import Document
from papistui.helpers.config import get_config


config = get_config()


def alias(self, field):
    """ Returns alternative representation for entries in field as defined in configuration

    :param field: field for which aliases are to be looked up in config
    :return str alias for original value
    """

    try:
        result = config["documentlist"]["aliases"][field][self.get(field)]
    except:
        try:
            result = config["documentlist"]["aliases"][field]["_default_"]
        except:
            result = ""

    return result

Document.alias = alias


def foreach(self, field, style, sep=" ", split=", "):
    """ Specify individual format for entries in list

    :param field: str document field/key to be used
    :param style: str style to be applied to each element in list
    :param sep: separator for each element in list, defaults to " "
    :param split: str used to split elements in fields of type str, defaults to ", "
    :return str evaluated string
    """

    try:
        if type(self[field]) == list:
            elements = self[field]
        elif type(self[field]) == str:
            elements = self[field].split(split)
        else:
            elements = str(self[field])

        results = []
        for element in elements:
            if element != "":
                results.append(style.replace("{}", element))

        return sep.join(results)
    except:
        return ""

Document.foreach = foreach


def forfile(self, string="*", sep=""):
    """ Return input for each file

    :param string: str to be returned, defaults to "*"
    :param sep: str used to separate elements, defaults to ""
    """

    files = self.get_files()
    if len(files) > 0:
        return sep.join([string for i in files])
    else:
        return ""

Document.forfile = forfile
