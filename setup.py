try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

import versioneer


config = {
    'description': 'Extend IPython with a suite of tools',
    'author': 'Matt Conley',
    'url': None,
    'download_url': None,
    'author_email': None,
    'version': '0.0.1',
    'install_requires': ['IPython', 'mpld3', 'contextlib2'], 
    'dependency_links': [],
    'packages': find_packages(),
    'scripts': [],
    'name': 'ipytools',
}

setup(**config)