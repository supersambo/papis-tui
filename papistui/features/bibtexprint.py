import io
import six
import re
from papis.document import Document
import pybtex.database.input.bibtex
import pybtex.database.input.bibyaml
import pybtex.plugin
import pybtex.errors
from papis.bibtex import to_bibtex
import papis.api as api


def format_reference(docs, style="plain", backend="plaintext", output="reference"):
    """ Very experimental citation formater

    :param docs: documents to be processed
    :param style: citation style, defaults to "plain"
    :param backend: str not yet implemented (only plaintext works) 'plaintext', 'html', 'latex' or 'markdown', defaults to "plaintext"
    :param output: str either 'reference' or 'intext' citation, defaults to "reference"
    """
    if type(docs) != list:
        docs = [docs]

    pybtex.errors.set_strict_mode(False)
    pybtex_style = pybtex.plugin.find_plugin("pybtex.style.formatting", style)()
    pybtex_backend = pybtex.plugin.find_plugin("pybtex.backends", backend)()
    pybtex_parser = pybtex.database.input.bibtex.Parser()

    bibtex = ""
    for doc in docs:
        bibtex += "\n" + to_bibtex(doc)

    data = pybtex_parser.parse_stream(six.StringIO(bibtex))
    data_formatted = pybtex_style.format_entries(six.itervalues(data.entries))
    out = io.StringIO()
    pybtex_backend.write_to_stream(data_formatted, out)
    value = out.getvalue()
    results = []

    if backend == "plaintext":
        lines = value.splitlines()
        for line in lines:
            if output == "reference":
                results.append(re.sub("^\[.*\]\s", "", line))
            if output == "intext":
                results.append(re.sub("^\[", "", re.sub("\]\s.*", "", line)))

    #currently only applied to one document at a time
    return results[0]

