# -*- coding: utf-8 -*-

import codecs
import os
import re
import urlparse

import gander


def load_resource_file(filename):
    dirpath =  os.path.dirname(gander.__file__)
    path = '%s/resources/%s' % (dirpath, filename)
    try:
        f = codecs.open(path, 'r', 'utf-8')
        content = f.read()
        f.close()
        return content
    except IOError:
        raise IOError("Couldn't open file %s" % path)
