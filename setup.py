import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="ELSA",
    version="0.3",
    author="Destin-informatique",
    author_email="christophe.dupriez@destin-informatique.com",
    url="http://www.destin-informatique.com",
    description="Monitoring de la production par lots",
    long_description=read('README.md'),
    packages=find_packages(),
    classifiers=[
        'Operating System :: POSIX',
        'Programming Language :: Python',
    ], install_requires=['python-barcode', 'requests', 'pySerial', 'rrdtool', 'web.py', 'pyownet', 'numpy', 'smbus2','influx_line_protocol']
)
