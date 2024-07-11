import papis.api as api
import re


def tag_document(doc, tags, tagfield):
    """Add or remove tag from document

    :param doc: document to be tagged
    :param tags: list of tags to be added or removed
    :param tagfield: key where tags are stored
    """

    if not doc[tagfield]:
        doc[tagfield] = []
    elif type(doc[tagfield]) == str:
        doc[tagfield] = [doc[tagfield]]

    for tag in tags:
        if tag[1] and tag[0] not in doc[tagfield]:
            doc[tagfield].append(tag[0])

        if not tag[1] and tag[0] in doc[tagfield]:
            doc[tagfield].remove(tag[0])

    doc.save()


def process_tags(tags):
    """Preprocess list of tags

    :param tags: list of tags
    :return list of tuples including tags and boolean to whether add (True) or remove (False)
    """
    result = []
    for tag in tags:
        if tag.endswith("-"):
            result.append((tag[:-1], False))
        elif tag.endswith("+"):
            result.append((tag[:-1], True))
        else:
            result.append((tag, True))
    return result
