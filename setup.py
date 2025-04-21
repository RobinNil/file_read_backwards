#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
]

test_requirements = [
    "mock",
]

setup(
    name='file_read_backwards',
    version='3.2.0',
    description="Memory efficient way of reading files line-by-line from the end of file",
    long_description=readme + '\n\n' + history,
    author="Robin Robin",
    author_email='robinsquare42@gmail.com',
    url='https://github.com/RobinNil/file_read_backwards',
    packages=[
        'file_read_backwards',
    ],
    package_dir={'file_read_backwards':
                 'file_read_backwards'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords='file_read_backwards',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
