# -*- coding: utf-8 -*-

import copy
import lxml.etree
import lxml.html

from gander.text import encode_value, inner_trim


def from_string(html):
    html = encode_value(html)
    doc = lxml.html.fromstring(html)
    return doc


def node_to_string(node):
    return lxml.etree.tostring(node)


def replace_tag(node, tag):
    node.tag = tag


def strip_tags(node, *tags):
    lxml.etree.strip_tags(node, *tags)


def get_element_by_id(node, idd):
    selector = '//*[@id="%s"]' % idd
    elems = node.xpath(selector)
    if elems:
        return elems[0]
    return None


def get_elements_by_tag(node, tag=None, attr=None, value=None,
                        childs=False):
    NS = "http://exslt.org/regular-expressions"
    # selector = tag or '*'
    selector = 'descendant-or-self::%s' % (tag or '*')
    if attr and value:
        selector = '%s[re:test(@%s, "%s", "i")]' % (selector, attr, value)
        #selector = '%s[%s="%s"]' % (selector, attr, value)
    #elems = node.cssselect(selector)
    elems = node.xpath(selector, namespaces={"re": NS})
    # remove the root node
    # if we have a selection tag
    if node in elems and (tag or childs):
        elems.remove(node)
    return elems

def appendChild(node, child):
    node.append(child)


def childNodes(node):
    return list(node)


def child_nodes_with_text(node):
    root = node
    # create the first text node
    # if we have some text in the node
    if root.text:
        t = lxml.html.HtmlElement()
        t.text = root.text
        t.tag = 'text'
        root.text = None
        root.insert(0, t)
    # loop childs
    for c, n in enumerate(list(root)):
        idx = root.index(n)
        # don't process texts nodes
        if n.tag == 'text':
            continue
        # create a text node for tail
        if n.tail:
            t = create_element(tag='text', text=n.tail, tail=None)
            root.insert(idx + 1, t)
    return list(root)


def text_to_p(text):
    return from_string(text)


def get_elements_by_tags(node, tags):
    selector = ','.join(tags)
    elems = node.cssselect(selector)
    # remove the root node
    # if we have a selection tag
    if node in elems:
        elems.remove(node)
    return elems


def create_element(tag='p', text=None, tail=None):
    t = lxml.html.HtmlElement()
    t.tag = tag
    t.text = text
    t.tail = tail
    return t


def get_comments(node):
    return node.xpath('//comment()')


def get_parent(node):
    return node.getparent()


def remove(node):
    parent = node.getparent()
    if parent is not None:
        if node.tail:
            prev = node.getprevious()
            if prev is None:
                if not parent.text:
                    parent.text = ''
                parent.text += u' ' + node.tail
            else:
                if not prev.tail:
                    prev.tail = ''
                prev.tail += u' ' + node.tail
        node.clear()
        parent.remove(node)


def get_tag(node):
    return node.tag


def get_text(node):
    txts = [i for i in node.itertext()]
    return inner_trim(u' '.join(txts).strip())


def previous_siblings(node):
    nodes = []
    for c, n in enumerate(node.itersiblings(preceding=True)):
        nodes.append(n)
    return nodes


def previous_sibling(node):
    nodes = []
    for c, n in enumerate(node.itersiblings(preceding=True)):
        nodes.append(n)
        if c == 0:
            break
    return nodes[0] if nodes else None


def next_sibling(node):
    nodes = []
    for c, n in enumerate(node.itersiblings(preceding=False)):
        nodes.append(n)
        if c == 0:
            break
    return nodes[0] if nodes else None


def is_text_node(node):
    return node.tag == 'text'


def get_attribute(node, attr=None):
    if attr:
        return node.attrib.get(attr, None)
    return attr


def set_attribute(node, attr=None, value=None):
    if attr and value:
        node.set(attr, value)


def outer_html(node):
    e0 = node
    if e0.tail:
        e0 = copy.deepcopy(e0)
        e0.tail = None
    return node_to_string(e0)
