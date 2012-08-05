# -*- coding: utf-8 -*-

from HTMLParser import HTMLParser

from gander import parser
from gander.text import inner_trim, StopWords


def format_text(top_node):
    remove_nodes_with_negative_scores(top_node)
    convert_links_to_text(top_node)
    replace_tags_with_text(top_node)
    remove_paragraphs_with_few_words(top_node)
    return convert_to_text(top_node)


def convert_to_text(top_node):
    txts = []
    for node in list(top_node):
        txt = parser.get_text(node)
        if txt:
            txt = HTMLParser().unescape(txt)
            txts.append(inner_trim(txt))
    return '\n\n'.join(txts)


def convert_links_to_text(top_node):
    """
    Cleans up and converts any nodes that  should be considered text into
    text.
    """
    parser.strip_tags(top_node, 'a')


def remove_nodes_with_negative_scores(top_node):
    """Remove elements with negative score attributes."""
    scored_items = top_node.cssselect("*[score]")
    for item in scored_items:
        score = int(item.attrib.get('score'), 0)
        if score < 1:
            item.getparent().remove(item)


def replace_tags_with_text(top_node):
    """
    Replace common tags with just text so we don't have any crazy
    formatting issues so replace <br>, <i>, <strong>, etc.... with whatever
    text is inside them code:
    http://lxml.de/api/lxml.etree-module.html#strip_tags.
    """
    parser.strip_tags(top_node, 'b', 'strong', 'i', 'br')


def remove_paragraphs_with_few_words(top_node):
    """
    Remove paragraphs that have less than x number of words,  would
    indicate that it's some sort of link.
    """
    all_nodes = parser.get_elements_by_tags(top_node, ['*'])
    all_nodes.reverse()
    for el in all_nodes:
        text = parser.get_text(el)
        stop_words = StopWords().get_stop_word_count(text)
        if stop_words.get_stop_word_count() < 3 \
            and len(parser.get_elements_by_tag(el, tag='object')) == 0 \
            and len(parser.get_elements_by_tag(el, tag='embed')) == 0:
            parser.remove(el)
        # TODO: Check if it is in the right place.
        else:
            trimmed = parser.get_text(el)
            if trimmed.startswith("(") and trimmed.endswith(")"):
                parser.remove(el)
