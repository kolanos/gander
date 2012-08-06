# -*- coding: utf-8 -*-

import copy
import re
import urlparse

from gander import parser
from gander.text import StopWords


def title(doc):
    """Return the document's title."""
    title = ''
    title_elem = parser.get_elements_by_tag(doc, tag='title')
    # no title found
    if title_elem is None or len(title_elem) == 0:
        return title
    # title elem found
    title_text = parser.get_text(title_elem[0])
    used_delimeter = False
    # split title with |
    if '|' in title_text:
        title_text = _split_title(title_text, "\\|")
        used_delimeter = True
    # split title with -
    if not used_delimeter and '-' in title_text:
        title_text = _split_title(title_text, " - ")
        used_delimeter = True
    # split title with »
    if not used_delimeter and u'»' in title_text:
        title_text = _split_title(title_text, "»")
        used_delimeter = True
    # split title with :
    if not used_delimeter and ':' in title_text:
        title_text = _split_title(title_text, ":")
        used_delimeter = True
    title = title_text.replace("&#65533;", "")
    return title


def _split_title(title, splitter):
    """Split the title, keep largest piece."""
    larger_text_length = 0
    larger_text_index = 0
    title_pieces = title.split(splitter)
    # find the largest title piece
    for i in range(len(title_pieces)):
        current = title_pieces[i]
        if len(current) > larger_text_length:
            larger_text_length = len(current)
            larger_text_index = i
    # replace content
    title = title_pieces[larger_text_index]
    return title.replace("&raquo;", u"»").strip()


def meta_favicon(doc):
    """Return the document's meta favicon."""
    kwargs = {'tag': 'link', 'attr': ' rel', 'value': 'icon'}
    meta = parser.get_elements_by_tag(doc, **kwargs)
    if meta:
        favicon = meta[0].attrib.get('href')
        return favicon
    return ''


def meta_lang(doc):
    """Extract content language from meta."""
    # we have a lang attribute in html
    attr = parser.get_attribute(doc, attr='lang')
    if attr is None:
        # look up for a Content-Language in meta
        kwargs = {'tag': 'meta', 'attr': ' http-equiv',
                  'value': 'content-language'}
        meta = parser.get_elements_by_tag(doc, **kwargs)
        if meta:
            attr = parser.get_attribute(meta[0], attr='content')
    if attr:
        value = attr[:2]
        if re.search('^[A-Za-z]{2}$', value):
            return value.lower()
    return None


def meta_content(doc, meta_name):
    """Extract a given meta content form document."""
    meta = doc.cssselect(meta_name)
    content = None
    if meta is not None and len(meta) > 0:
        content = meta[0].attrib.get('content')
    if content:
        return content.strip()
    return ''


def meta_description(doc):
    """Return the documents meta description."""
    return meta_content(doc, "meta[name=description]")


def meta_keywords(doc):
    """Return document's meta keywords."""
    return meta_content(doc, "meta[name=keywords]")


def canonical_link(doc):
    """Return document's canonical link."""
    kwargs = {'tag': 'link', 'attr': 'rel', 'value': 'canonical'}
    meta = parser.get_elements_by_tag(doc, **kwargs)
    if meta is not None and len(meta) > 0:
        href = meta[0].attrib.get('href')
        if href:
            href = href.strip()
            return href
    return ''


def domain(url):
    o = urlparse.urlparse(url)
    return o.hostname


def tags(node):
    """Return anchors with rel="tag" attribute."""
    # Node doesn't have chidren
    if len(list(node)) == 0:
        return set()
    # Alternate selector: "a[rel=tag], a[href*=/tag/]"
    elements = node.cssselect("a[rel=tag]")
    if elements is None:
        return set()
    tags = []
    for el in elements:
        tag = parser.get_text(el)
        if tag:
            tags.append(tag)
    return set(tags)


def calculate_best_node_based_on_clustering(doc):
    top_node = None
    check_nodes = nodes_to_check(doc)
    starting_boost = float(1.0)
    cnt = 0
    i = 0
    parent_nodes = set()
    nodes_with_text = []
    for node in check_nodes:
        node_text = parser.get_text(node)
        word_stats = StopWords().get_stop_word_count(node_text)
        high_link_density = is_high_link_density(node)
        if word_stats.get_stop_word_count() > 2 and not high_link_density:
            nodes_with_text.append(node)
    number_of_nodes = len(nodes_with_text)
    negative_scoring = 0
    bottom_nodes_for_negative_score = float(number_of_nodes) * 0.25
    for node in nodes_with_text:
        boost_score = float(0)
        # boost
        if ok_to_boost(node):
            if cnt >= 0:
                boost_score = float((1.0 / starting_boost) * 50)
                starting_boost += 1
        # number_of_nodes
        if number_of_nodes > 15:
            if (number_of_nodes - i) <= bottom_nodes_for_negative_score:
                booster = float(bottom_nodes_for_negative_score - \
                        (number_of_nodes - i))
                boost_score = float(-pow(booster, float(2)))
                negscore = -abs(boost_score) + negative_scoring
                if negscore > 40:
                    boost_score = float(5)
        node_text = parser.get_text(node)
        word_stats = StopWords().get_stop_word_count(node_text)
        upscore = int(word_stats.get_stop_word_count() + boost_score)
        # parent node
        parent_node = parser.get_parent(node)
        update_score(parent_node, upscore)
        update_node_count(node.getparent(), 1)
        if node.getparent() not in parent_nodes:
            parent_nodes.add(node.getparent())
        # parentparent node
        parent_parent_node = parser.get_parent(parent_node)
        if parent_parent_node is not None:
            update_node_count(parent_parent_node, 1)
            update_score(parent_parent_node, upscore / 2)
            if parent_parent_node not in parent_nodes:
                parent_nodes.add(parent_parent_node)
        cnt += 1
        i += 1
    top_node_score = 0
    for e in parent_nodes:
        score = get_score(e)
        if score > top_node_score:
            top_node = e
            top_node_score = score
        if top_node is None:
            top_node = e
    return top_node


def ok_to_boost(node):
    """\
    A lot of times the first paragraph might be the caption under an image
    so we'll want to make sure if we're going to boost a parent node that
    it should be connected to other paragraphs,
    at least for the first n paragraphs so we'll want to make sure that
    the next sibling is a paragraph and has at
    least some substatial weight to it
    """
    para = "p"
    steps_away = 0
    minimum_stop_word_count = 5
    max_steps_away_from_node = 3
    nodes = walk_siblings(node)
    for current_node in nodes:
        # p
        if current_node.tag == para:
            if steps_away >= max_steps_away_from_node:
                return False
            para_text = parser.get_text(current_node)
            word_stats = StopWords().get_stop_word_count(para_text)
            if word_stats.get_stop_word_count > minimum_stop_word_count:
                return True
            steps_away += 1
    return False


def walk_siblings(node):
    current_sibling = parser.previous_sibling(node)
    b = []
    while current_sibling is not None:
        b.append(current_sibling)
        previous_sibling = parser.previous_sibling(current_sibling)
        if previous_sibling is not None:
            current_sibling = previous_sibling
        else:
            current_sibling = None
    return b


def add_siblings(top_node):
    sibling_paragraphs_baseline_score = siblings_baseline_score(top_node)
    results = walk_siblings(top_node)
    for current_node in results:
        ps = sibling_content(current_node, sibling_paragraphs_baseline_score)
        for p in ps:
            top_node.insert(0, p)
    return top_node


def sibling_content(current_sibling, sibling_paragraphs_baseline_score):
    """
    Adds any siblings that may have a decent score to this node
    """
    if current_sibling.tag == 'p' \
            and len(parser.get_text(current_sibling)) > 0:
        e0 = current_sibling
        if e0.tail:
            e0 = copy.deepcopy(e0)
            e0.tail = ''
        return [e0]
    else:
        potential_paragraphs = parser.get_elements_by_tag(current_sibling, tag='p')
        if potential_paragraphs is None:
            return None
        else:
            ps = []
            for first_paragraph in potential_paragraphs:
                text = parser.get_text(first_paragraph)
                if len(text) > 0:
                    word_stats = StopWords().get_stop_word_count(text)
                    paragraph_score = word_stats.get_stop_word_count()
                    sibling_baseline_score = float(.30)
                    high_link_density = is_high_link_density(first_paragraph)
                    score = float(sibling_paragraphs_baseline_score * sibling_baseline_score)
                    if score < paragraph_score and not high_link_density:
                        p = parser.create_element(tag='p', text=text, tail=None)
                        ps.append(p)
            return ps


def siblings_baseline_score(top_node):
    """
    We could have long articles that have tons of paragraphs
    so if we tried to calculate the base score against
    the total text score of those paragraphs it would be unfair.
    So we need to normalize the score based on the average scoring
    of the paragraphs within the top node.
    For example if our total score of 10 paragraphs was 1000
    but each had an average value of 100 then 100 should be our base.
    """
    base = 100000
    number_of_paragraphs = 0
    score_of_paragraphs = 0
    nodes_to_check = parser.get_elements_by_tag(top_node, tag='p')
    for node in nodes_to_check:
        node_text = parser.get_text(node)
        word_stats = StopWords().get_stop_word_count(node_text)
        high_link_density = is_high_link_density(node)
        if word_stats.get_stop_word_count() > 2 and not high_link_density:
            number_of_paragraphs += 1
            score_of_paragraphs += word_stats.get_stop_word_count()
    if number_of_paragraphs > 0:
        base = score_of_paragraphs / number_of_paragraphs
    return base


def update_score(node, add_to_score):
    """\
    Adds a score to the score Attribute we put on divs we'll get the current
    score then add the score we're passing in to the current.
    """
    current_score = 0
    score_string = node.attrib.get('score')
    if score_string:
        current_score = int(score_string)
    new_score = current_score + add_to_score
    node.set("score", str(new_score))


def update_node_count(node, add_to_count):
    """\
    Stores how many decent nodes are under a parent node.
    """
    current_score = 0
    count_string = node.attrib.get('nodes')
    if count_string:
        current_score = int(count_string)
    new_score = current_score + add_to_count
    node.set("nodes", str(new_score))


def is_high_link_density(e):
    """
    Checks the density of links within a node, is there not much text and
    most of it contains linky shit? if so it's no good.
    """
    links = parser.get_elements_by_tag(e, tag='a')
    if links is None or len(links) == 0:
        return False
    text = parser.get_text(e)
    words = text.split(' ')
    number_of_words = float(len(words))
    sb = []
    for link in links:
        sb.append(parser.get_text(link))
    link_text = ''.join(sb)
    link_words = link_text.split(' ')
    number_of_link_words = float(len(link_words))
    number_of_links = float(len(links))
    link_divisor = float(number_of_link_words / number_of_words)
    score = float(link_divisor * number_of_links)
    if score >= 1.0:
        return True
    return False
    # return True if score > 1.0 else False


def get_score(node):
    """Returns the score as an integer from this node."""
    return score_from_node(node) or 0


def score_from_node(node):
    score = node.attrib.get('score')
    if not score:
        return None
    return int(score)


def nodes_to_check(doc):
    """
    Returns a list of nodes we want to search on like paragraphs and tables.
    """
    nodes_to_check = []
    for tag in ['p', 'pre', 'td']:
        items = parser.get_elements_by_tag(doc, tag=tag)
        nodes_to_check += items
    return nodes_to_check


def is_table_tag_and_no_paragraphs_exist(e):
    sub_paragraphs = parser.get_elements_by_tag(e, tag='p')
    for p in sub_paragraphs:
        txt = parser.get_text(p)
        if len(txt) < 25:
            parser.remove(p)
    sub_paragraphs2 = parser.get_elements_by_tag(e, tag='p')
    if len(sub_paragraphs2) == 0 and e.tag is not "td":
        return True
    return False


def node_score_threshold_met(node, e):
    top_node_score = get_score(node)
    current_node_score = get_score(e)
    threshold_score = float(top_node_score * .08)
    if current_node_score < threshold_score and e.tag != 'td':
        return False
    return True


def cleanup(target_node):
    """
    Remove any divs that looks like non-content,
    Clusters of links, or paras with no gusto.
    """
    node = add_siblings(target_node)
    for e in node.getchildren():
        if e.tag != 'p':
            if is_high_link_density(e) \
                or is_table_tag_and_no_paragraphs_exist(e) \
                or not node_score_threshold_met(node, e):
                parser.remove(e)
    return node
