=====
Usage
=====

To use file_read_backwards in a project::

    #!/usr/bin/env python

    from __future__ import print_function
    from file_read_backwards import FileReadBackwards

    f = FileReadBackwards("/tmp/file", encoding="utf-8")

    # getting lines by lines starting from the last line up
    for l in f:
        print(l)

    # do it again
    for l in f:
        print(l)
