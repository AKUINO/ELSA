import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="ELSA",
    version="0.1",
    author="Destin-informatique",
    author_email="christophe.dupriez@destin-informatique.com",
    url="http://www.destin-informatique.com",
    description="Monitoring de la production par lots",
    long_description=read('README.md'),
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python',
    ], install_requires=['pyBarcode', 'requests', 'serial', 'rrdtool', 'unicodecsv', 'web.py', 'pyownet']
)
