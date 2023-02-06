import papis.api as api
from papis.document import sort
import re


def sort_group(docs, key):
    """ Return list of lists containing documents with equal values in key

    :param docs: list of documents
    :param key: key according to which documents are grouped
    """
    groups = []
    g = []
    for idx, doc in enumerate(docs):
        g.append(doc)
        if idx + 1 < len(docs):
            if docs[idx][key] != docs[idx + 1][key]:
                groups.append(g)
                g = []
        else:
            groups.append(g)
    return groups


def process_sortkeys(sortkeys):
    """ Preprocess string(s) of sortkeys

    :param sortkeys: list or string containing sortkeys
    :return list of tuples containing key and boolean (key, decreasing)
    """

    if type(sortkeys) == str:
        sortkeys = sortkeys.split()
    result = []
    for key in sortkeys:
        if key.endswith("-"):
            result.append((key[:-1], True))
        elif key.endswith("+"):
            result.append((key[:-1], False))
        else:
            result.append((key, False))
    return result


def sort_multiple_keys(docs, sortkeys):
    """
    Sort documents based on multiple keys 
    Trailing '-' minus indicates decreasing sort

    :param docs: list of documents
    :param sortkeys: list or string containing sortkeys
    :return list of sorted documents
    """

    keys = process_sortkeys(sortkeys)
    docs = sort(docs, keys[0][0], keys[0][1])
    result = []
    idx = 0
    while idx + 1 < len(keys):
        nextsort = []
        for group in sort_group(docs, keys[idx][0]):
            group_sorted = sort(group, keys[idx + 1][0], keys[idx + 1][1])
            for doc in group_sorted:
                nextsort.append(doc)
        docs = nextsort
        idx += 1
    return docs

