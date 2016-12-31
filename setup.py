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
    version='1.1.0',
    description="Memory efficient way of reading files line-by-line from the end of file",
    long_description=readme + '\n\n' + history,
    author="Robin Robin",
    author_email='robin81@gmail.com',
    url='https://github.com/robin81/file_read_backwards',
    packages=[
        'file_read_backwards',
    ],
    package_dir={'file_read_backwards':
                 'file_read_backwards'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='file_read_backwards',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
