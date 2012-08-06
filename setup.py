import os
from setuptools import setup

import gander


def read(fname):

    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return ''

setup(
    name=gander.__title__,
    version=gander.__version__,
    description="Tools to extract content from HTML documents",
    long_description=read("README.rst"),
    keywords='html document content extraction parsing',
    author=gander.__author__,
    author_email=gander.__email__,
    url='https://github.com/kolanos/gander',
    license=gander.__license__,
    packages=['gander'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['lxml']
)
