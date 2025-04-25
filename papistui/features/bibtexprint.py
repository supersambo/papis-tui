import io
import six
import re

from papis.bibtex import to_bibtex


def format_reference(docs, style="plain", backend="plaintext", output="reference"):
    """ Very experimental citation formater

    :param docs: documents to be processed
    :param style: citation style, defaults to "plain"
    :param backend: str not yet implemented (only plaintext works)
        'plaintext', 'html', 'latex' or 'markdown'. (defaults to 'plaintext')
    :param output: str either 'reference' or 'intext' citation, defaults to "reference"
    """
    if type(docs) is not list:
        docs = [docs]

    from pybtex.errors import set_strict_mode

    set_strict_mode(False)

    from pybtex.plugin import find_plugin

    pybtex_style = find_plugin("pybtex.style.formatting", style)()
    pybtex_backend = find_plugin("pybtex.backends", backend)()

    from pybtex.database.input.bibtex import Parser

    pybtex_parser = Parser()

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
                results.append(re.sub(r"^\[.*\]\s", "", line))
            if output == "intext":
                results.append(re.sub(r"^\[", "", re.sub(r"\]\s.*", "", line)))

    # currently only applied to one document at a time
    return results[0]
