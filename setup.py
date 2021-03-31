# -*- coding: utf-8 -*-
#######################################################################
# License: GNU General Public License v3.0                            #
# Homepage: https://github.com/tasooshi/pukpuk/                       #
# Version: 2.0.1                                                        #
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
    version='2.0.1',
    author='tasooshi',
    author_email='tasooshi@pm.me',
    description='HTTP services discovery toolkit',
    license='GNU General Public License v3.0',
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
        'pyOpenSSL==20.0.1',
        'dnspython==2.1.0',
        'requests==2.25.1',
        'Pillow==8.1.1',
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
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ]
)
