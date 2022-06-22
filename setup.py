# -*- coding: utf-8 -*-
#######################################################################
# License: MIT License                                                #
# Homepage: https://github.com/tasooshi/pukpuk/                       #
# Version: 2.0.6                                                      #
#######################################################################

from __future__ import (
    absolute_import,
    unicode_literals,
)

import setuptools


with open('README.md') as f:
    long_description = f.read()


setuptools.setup(
    name='pukpuk',
    version='2.0.6',
    author='tasooshi',
    author_email='tasooshi@pm.me',
    description='HTTP services discovery toolkit',
    license='MIT License',
    keywords=[
        'HTTP',
        'scanner',
        'discovery',
    ],
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/tasooshi/pukpuk/',
    packages=setuptools.find_packages(),
    install_requires=(
        'pyOpenSSL==22.0.0',
        'dnspython==2.2.1',
        'requests==2.28.0',
        'Pillow==9.1.1',
        'PySocks==1.7.1',
    ),
    entry_points={
        'console_scripts': (
            'pukpuk=pukpuk:entry_point',
        ),
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ]
)
