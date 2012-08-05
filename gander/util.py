# -*- coding: utf-8 -*-

import codecs
import hashlib
import os
import re
import urlparse

import gander


class BuildURL(object):
    def __init__(self, url, finalurl=None):
        self.url = url
        self.finalurl = finalurl

    def get_hostname(self, o):
        if o.hostname:
            return o.hotname
        elif self.finalurl:
            oo = urlparse.urlparse(self.finalurl)
            if oo.hostname:
                return oo.hostname
        return None

    def get_scheme(self, o):
        if o.scheme:
            return o.scheme
        elif self.finalurl:
            oo = urlparse.urlparse(self.finalurl)
            if oo.scheme:
                return oo.scheme
        return 'http'

    def get_url(self):
        url_obj = urlparse.urlparse(self.url)
        scheme = self.get_scheme(url_obj)
        hostname = self.get_hostname(url_obj)


class FileHelper(object):
    @classmethod
    def load_resource_file(self, filename):
        dirpath =  os.path.dirname(gander.__file__)
        path = '%s/resources/%s' % (dirpath, filename)
        try:
            f = codecs.open(path, 'r', 'utf-8')
            content = f.read()
            f.close()
            return content
        except IOError:
            raise IOError("Couldn't open file %s" % path)


class ParsingCandidate(object):
    def __init__(self, url_string, linkhash, url):
        self.url_string = url_string
        self.linkhash = linkhash
        self.url = url


class URLHelper(object):
    @classmethod
    def get_cleaned_url(self, url_to_crawl):
        # replace shebang is urls
        final_url = url_to_crawl.replace('#!', '?_escaped_fragment_=') \
                    if '#!' in url_to_crawl else url_to_crawl
        linkhash = hashlib.md5(final_url).hexdigest()
        return ParsingCandidate(final_url, linkhash, final_url)


class StringSplitter(object):
    def __init__(self, pattern):
        self.pattern = re.compile(pattern)

    def split(self, string):
        if not string:
            return []
        return self.pattern.split(string)


class StringReplacement(object):
    def __init__(self, pattern, replace_with):
        self.pattern = pattern
        self.replace_with = replace_with

    def replace_all(self, string):
        if not string:
            return u''
        return string.replace(self.pattern, self.replace_with)


class ReplaceSequence(object):
    def __init__(self):
        self.replacements = []

    def create(self, first_pattern, replace_with=None):
        result = StringReplacement(first_pattern, replace_with or u'')
        self.replacements.append(result)
        return self

    def append(self, pattern, replace_with=None):
        return self.create(pattern, replace_with)

    def replace_all(self, string):
        if not string: 
            return u''
        mutated_string = string
        for rp in self.replacements:
            mutated_string = rp.replace_all(mutated_string)
        return mutated_string
