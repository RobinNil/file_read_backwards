===============================
file_read_backwards
===============================


.. image:: https://img.shields.io/pypi/v/file_read_backwards.svg
        :target: https://pypi.python.org/pypi/file_read_backwards

.. image:: https://img.shields.io/travis/robin81/file_read_backwards.svg
        :target: https://travis-ci.org/robin81/file_read_backwards

.. image:: https://readthedocs.org/projects/file-read-backwards/badge/?version=latest
        :target: https://file-read-backwards.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/robin81/file_read_backwards/shield.svg
     :target: https://pyup.io/repos/github/robin81/file_read_backwards/
     :alt: Updates


Memory efficient way of reading files line-by-line from the end of file


* Free software: MIT license
* Documentation: https://file-read-backwards.readthedocs.io.


Features
--------

This package is for reading file backward line by line as unicode in a memory efficient manner. Think of it as a `tac` command for Python.

It currently supports ascii and utf-8 encodings. Other encodings have not been tested.

It supports "\\r", "\\r\\n", and "\\n" as new lines.

Please see :doc:`usage` for examples.

Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

