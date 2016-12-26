=====
Usage
=====

An example of using `file_read_backwards` for `python2.7`::

    #!/usr/bin/env python2.7

    from file_read_backwards import FileReadBackwards

    f = FileReadBackwards("/tmp/file", encoding="utf-8")

    # getting lines by lines starting from the last line up
    for l in f:
        print l

    # do it again
    for l in f:
        print l


Another example using `python3.3`::

    #!/usr/bin/env python3.3

    from file_read_backwards import FileReadBackwards

    f = FileReadBackwards("/tmp/file", encoding="utf-8")

    # getting lines by lines starting from the last line up
    for l in f:
        print(l)

    # do it again
    for l in f:
        print(l)
