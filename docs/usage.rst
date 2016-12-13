=====
Usage
=====

To use file_read_backwards in a project::

    from __future__ import print_function
    import file_read_backwards

    f = FileReadBackwards("/tmp/file", encoding="utf-8")

    # getting lines by lines starting from the last line up
    for l in f:
        print(l)

    # do it again
    for l in f:
        print(l)
