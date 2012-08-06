# -*- coding: utf-8 -*-

from gander import parser


REGEX_REMOVE_NODES = (
    "^side$|combx|retweet|mediaarticlerelated|menucontainer|navbar"
    "|comment|PopularQuestions|contact|foot|footer|Footer|footnote"
    "|cnn_strycaptiontxt|links|meta$|scroll|shoutbox|sponsor"
    "|tags|socialnetworking|socialNetworking|cnnStryHghLght"
    "|cnn_stryspcvbx|^inset$|pagetools|post-attributes"
    "|welcome_form|contentTools2|the_answers"
    "|communitypromo|runaroundLeft|subscribe|vcard|articleheadings"
    "|date|^print$|popup|author-dropdown|tools|socialtools|byline"
    "|konafilter|KonaFilter|breadcrumbs|^fn$|wp-caption-text"
    "|source|legende|ajoutVideo|timestamp"
)
REGEX_NS = "http://exslt.org/regular-expressions"
QUERY_IDS = "//*[re:test(@id, '%s', 'i')]" % REGEX_REMOVE_NODES
QUERY_CLASSES = "//*[re:test(@class, '%s', 'i')]" % REGEX_REMOVE_NODES
QUERY_NAMES = "//*[re:test(@name, '%s', 'i')]" % REGEX_REMOVE_NODES
DIV_TO_ELEMENTS_PATTERN = r"<(a|blockquote|dl|div|img|ol|p|pre|table|ul)"
CAPTION_PATTERN = "^caption$"
GOOGLE_PATTERN = " google "
ENTRIES_PATTERN = "^[^entry-]more.*$"
FACEBOOK_PATTERN = "[^-]facebook"
TWITTER_PATTERN = "[^-]twitter"
TABS_AND_NEWLINES = [("\n", "\n\n"), ("\t", ""), ("^\\s+$", "")]


def clean(doc):
    doc_to_clean = doc
    doc_to_clean = clean_em_tags(doc_to_clean)
    doc_to_clean = remove_drop_caps(doc_to_clean)
    doc_to_clean = remove_script_and_style(doc_to_clean)
    doc_to_clean = clean_bad_tags(doc_to_clean)
    doc_to_clean = remove_nodes_via_regex(doc_to_clean, CAPTION_PATTERN)
    doc_to_clean = remove_nodes_via_regex(doc_to_clean, GOOGLE_PATTERN)
    doc_to_clean = remove_nodes_via_regex(doc_to_clean, ENTRIES_PATTERN)
    doc_to_clean = remove_nodes_via_regex(doc_to_clean, FACEBOOK_PATTERN)
    doc_to_clean = remove_nodes_via_regex(doc_to_clean, TWITTER_PATTERN)
    doc_to_clean = clean_span_in_p(doc_to_clean)
    doc_to_clean = convert_div_to_p(doc_to_clean, 'div')
    doc_to_clean = convert_div_to_p(doc_to_clean, 'span')
    return doc_to_clean


def clean_em_tags(doc):
    ems = parser.get_elements_by_tag(doc, tag='em')
    for node in ems:
        images = parser.get_elements_by_tag(node, tag='img')
        if len(images) == 0:
            node.drop_tag()
    return doc


def remove_drop_caps(doc):
    items = doc.cssselect("span[class~=dropcap], span[class~=drop_cap]")
    for item in items:
        item.drop_tag()
    return doc


def remove_script_and_style(doc):
    # remove scripts
    scripts = parser.get_elements_by_tag(doc, tag='script')
    for item in scripts:
        parser.remove(item)
    # remove styles
    styles = parser.get_elements_by_tag(doc, tag='style')
    for item in styles:
        parser.remove(item)
    # remove comments
    comments = parser.get_comments(doc)
    for item in comments:
        parser.remove(item)
    return doc


def clean_bad_tags(doc):
    # ids
    naughty_list = doc.xpath(QUERY_IDS, namespaces={'re': REGEX_NS})
    for node in naughty_list:
        parser.remove(node)
    # class
    naughty_classes = doc.xpath(QUERY_CLASSES,
                                namespaces={'re': REGEX_NS})
    for node in naughty_classes:
        parser.remove(node)
    # name
    naughty_names = doc.xpath(QUERY_NAMES,
                              namespaces={'re': REGEX_NS})
    for node in naughty_names:
        parser.remove(node)
    return doc


def remove_nodes_via_regex(doc, pattern):
    for selector in ['id', 'class']:
        reg = "//*[re:test(@%s, '%s', 'i')]" % (selector, pattern)
        naughty_list = doc.xpath(reg, namespaces={'re': REGEX_NS})
        for node in naughty_list:
            parser.remove(node)
    return doc


def clean_span_in_p(doc):
    spans = doc.cssselect('p > span')
    for item in spans:
        item.drop_tag()
    return doc

def get_flushed_buffer(replacement_text, doc):
    return parser.text_to_p(replacement_text)


def get_replacement_nodes(doc, div):
    replacement_text = []
    nodes_to_return = []
    nodes_to_remove = []
    childs = parser.child_nodes_with_text(div)
    for kid in childs:
        # node is a p
        # and already have some replacement text
        if parser.get_tag(kid) == 'p' and len(replacement_text) > 0:
            new_node = get_flushed_buffer(''.join(replacement_text),
                                               doc)
            nodes_to_return.append(new_node)
            replacement_text = []
            nodes_to_return.append(kid)
        # node is a text node
        elif parser.is_text_node(kid):
            kid_text_node = kid
            kid_text = parser.get_text(kid)
            replace_text = kid_text
            for p, w in TABS_AND_NEWLINES:
                replace_text = replace_text.replace(p, w)
            if len(replace_text) > 1:
                prev_sib_node = parser.previous_sibling(kid_text_node)
                while prev_sib_node is not None \
                    and parser.get_tag(prev_sib_node) == "a" \
                    and parser.get_attribute(prev_sib_node, 'grv-usedalready') != 'yes':
                    outer = " " + parser.outer_html(prev_sib_node) + " "
                    replacement_text.append(outer)
                    nodes_to_remove.append(prev_sib_node)
                    parser.set_attribute(prev_sib_node,
                                         attr='grv-usedalready',
                                         value='yes')
                    prev = parser.previous_sibling(prev_sib_node)
                    prev_sib_node = prev if prev is not None else None
                # append replace_text
                replacement_text.append(replace_text)
                #
                next_Sib_node = parser.next_sibling(kid_text_node)
                while next_Sib_node is not None \
                    and parser.get_tag(next_Sib_node) == "a" \
                    and parser.get_attribute(next_Sib_node, 'grv-usedalready') != 'yes':
                    outer = " " + parser.outer_html(next_Sib_node) + " "
                    replacement_text.append(outer)
                    nodes_to_remove.append(next_Sib_node)
                    parser.set_attribute(next_Sib_node,
                                         attr='grv-usedalready',
                                         value='yes')
                    next = parser.next_sibling(next_Sib_node)
                    prev_sib_node = next if next is not None else None
        # otherwise
        else:
            nodes_to_return.append(kid)
    # flush out anything still remaining
    if len(replacement_text) > 0:
        new_node = get_flushed_buffer(''.join(replacement_text), doc)
        nodes_to_return.append(new_node)
        replacement_text = []
    for n in nodes_to_remove:
        parser.remove(n)
    return nodes_to_return


def replace_elements_with_p(doc, div):
    parser.replace_tag(div, 'p')


def convert_div_to_p(doc, dom_type):
    bad_divs = 0
    else_divs = 0
    divs = parser.get_elements_by_tag(doc, tag=dom_type)
    tags = ['a', 'blockquote', 'dl', 'div', 'img', 'ol', 'p', 'pre',
            'table', 'ul']
    for div in divs:
        items = parser.get_elements_by_tags(div, tags)
        if div is not None and len(items) == 0:
            replace_elements_with_p(doc, div)
            bad_divs += 1
        elif div is not None:
            replace_nodes = get_replacement_nodes(doc, div)
            div.clear()
            for c, n in enumerate(replace_nodes):
                div.insert(c, n)
            else_divs += 1
    return doc
