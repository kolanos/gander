# -*- coding: utf-8 -*-

import re
import string

from .encoding import UnicodeDecodeError, smart_str, smart_unicode
from .util import FileHelper

TABSSPACE = re.compile(r'[\s\t]+')


def inner_trim(s):
    if isinstance(s, (unicode, str)):
        # remove tab and white space
        s = re.sub(TABSSPACE, ' ', s)
        s = ''.join(s.splitlines())
        return s.strip()
    return ''


def encode_value(s):
    orig = s
    try:
        s = smart_unicode(s)
    except (UnicodeEncodeError, UnicodeDecodeError):
        s = smart_str(s)
    except:
        s = orig
    return s


class WordStats(object):
    def __init__(self):
        # total number of stopwords or
        # good words that we can calculate
        self.stop_word_count = 0

        # total number of words on a node
        self.word_count = 0

        # holds an actual list
        # of the stop words we found
        self.stop_words = []

    def get_stop_words(self):
        return self.stop_words

    def set_stop_words(self, words):
        self.stop_words = words

    def get_stop_word_count(self):
        return self.stop_word_count

    def set_stop_word_count(self, wordcount):
        self.stop_word_count = wordcount

    def get_word_count(self):
        return self.word_count

    def set_word_count(self, cnt):
        self.word_count = cnt


class StopWords(object):
    def __init__(self, language='en'):
        self.PUNCTUATION = re.compile("[^\\p{Ll}\\p{Lu}\\p{Lt}\\p{Lo}\\p{Nd}\\p{Pc}\\s]")
        # TODO replace 'x' with class
        # to generate dynamic path for file to load
        path = 'text/stopwords-%s.txt' % language
        self.STOP_WORDS = set(FileHelper.load_resource_file(path).splitlines())

    def remove_punctuation(self, content):
        # code taken form
        # http://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        table = string.maketrans("", "")
        return content.translate(table, string.punctuation)

    def get_stop_word_count(self, content):
        if not content:
            return WordStats()
        ws = WordStats()
        stripped_input = self.remove_punctuation(content)
        candidate_words = stripped_input.split(' ')
        overlapping_stop_words = []
        for w in candidate_words:
            if w.lower() in self.STOP_WORDS:
                overlapping_stop_words.append(w.lower())
        ws.set_word_count(len(candidate_words))
        ws.set_stop_word_count(len(overlapping_stop_words))
        ws.set_stop_words(overlapping_stop_words)
        return ws
