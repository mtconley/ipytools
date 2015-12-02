try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

import versioneer

import glob, shutil, os


config = {
    'description': 'Extend IPython with a suite of tools',
    'author': 'Matt Conley',
    'url': 'https://github.com/mtconley/ipytools',
    'download_url': 'https://github.com/mtconley/ipytools.git',
    'author_email': None,
    'version': '0.0.1',
    'install_requires': ['IPython', 'mpld3'], 
    'dependency_links': [],
    'packages': find_packages(),
    'scripts': [],
    'name': 'ipytools',
}


def install_magics(directory):

    magics = os.path.join(os.getcwd(), 'ipytools', 'magics', '*')
    files = glob.glob(magics)
    for src in files:
        name = os.path.basename(src)
        shutil.copy(src, directory)

def install_templates(directory):

    if not os.path.exists(directory):
        tpl_dir = os.path.join(directory, 'templates')
        os.mkdir(tpl_dir)
    directory = os.path.join(directory, 'templates')
    templates = os.path.join(os.getcwd(), 'ipytools', 'nbconvert_templates', '*')
    files = glob.glob(templates)
    for src in files:
        name = os.path.basename(src)
        shutil.copy(src, directory)


setup(**config)

directory = os.path.join(os.environ['HOME'], '.ipython', 'extensions')
install_magics(directory)
install_templates(directory)