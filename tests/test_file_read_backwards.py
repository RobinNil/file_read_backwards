#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `file_read_backwards` module."""

import itertools
import os
import tempfile
import unittest

from collections import deque

from file_read_backwards.file_read_backwards import FileReadBackwards
from file_read_backwards.file_read_backwards import supported_encodings
from file_read_backwards.buffer_work_space import new_lines


# doing this xrange/range dance so that we don't need to add additional dependencies of future or six modules
try:
    xrange
except NameError:
    xrange = range


class TestFileReadBackwards(unittest.TestCase):

    """Class that contains various test cases for actual FileReadBackwards usage."""

    @staticmethod
    def write(t, s, encoding="utf-8"):
        """A helper method to write out string s in specified encoding."""
        t.write(s.encode(encoding))

    def test_with_completely_empty_file(self):
        """Test with a completely empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as t:
            pass
        f = FileReadBackwards(t.name)
        expected_lines = deque()
        lines_read = deque()
        for l in f:
            lines_read.appendleft(l)
        self.assertEqual(expected_lines, lines_read)

    def test_file_with_a_single_new_line_char_with_different_encodings(self):
        """Test a file with a single new line character."""
        for encoding, new_line in itertools.product(supported_encodings, new_lines):
            with tempfile.NamedTemporaryFile(delete=False) as t:
                TestFileReadBackwards.write(t, new_line, encoding)
            f = FileReadBackwards(t.name)
            expected_lines = deque([""])
            lines_read = deque()
            for l in f:
                lines_read.appendleft(l)
            self.assertEqual(
                expected_lines,
                lines_read,
                msg="Test with {0} encoding with {1} as newline".format(encoding, repr(new_line)))
            os.unlink(t.name)

    def test_file_with_one_line_of_text_with_accented_char_followed_by_a_new_line(self):
        """Test a file with a single line of text with accented char followed by a new line."""
        b = b'Caf\xc3\xa9'  # accented e in utf-8
        s = b.decode("utf-8")
        for new_line in new_lines:
            with tempfile.NamedTemporaryFile(delete=False) as t:
                TestFileReadBackwards.write(t, s)
                TestFileReadBackwards.write(t, new_line)
            f = FileReadBackwards(t.name)
            expected_lines = deque([s])
            lines_read = deque()
            for l in f:
                lines_read.appendleft(s)
            self.assertEqual(expected_lines, lines_read, msg="Test with {0} as newline".format(repr(new_line)))
            os.unlink(t.name)

    def test_file_with_one_line_of_text_followed_by_a_new_line_with_different_encodings(self):
        """Test a file with just one line of text followed by a new line."""
        for encoding, new_line in itertools.product(supported_encodings, new_lines):
            with tempfile.NamedTemporaryFile(delete=False) as t:
                TestFileReadBackwards.write(t, "something{0}".format(new_line), encoding)
            f = FileReadBackwards(t.name)
            expected_lines = deque(["something"])
            lines_read = deque()
            for l in f:
                lines_read.appendleft(l)
            self.assertEqual(
                expected_lines,
                lines_read,
                msg="Test with {0} encoding with {1} as newline".format(encoding, repr(new_line)))
            os.unlink(t.name)

    def test_file_with_varying_number_of_new_lines_and_some_text_in_chunk_size(self):
        """Test a file with varying number of new lines and text of size custom chunk_size."""
        chunk_size = 3
        s = "t"
        for number_of_new_lines in xrange(21):
            for new_line in new_lines:  # test with variety of new lines
                with tempfile.NamedTemporaryFile(delete=False) as t:
                    TestFileReadBackwards.write(t, new_line * number_of_new_lines)
                    TestFileReadBackwards.write(t, s * chunk_size)
                f = FileReadBackwards(t.name, chunk_size=chunk_size)
                expected_lines = deque()
                for _ in xrange(number_of_new_lines):
                    expected_lines.append("")
                expected_lines.append(s * chunk_size)
                lines_read = deque()
                for l in f:
                    lines_read.appendleft(l)
                self.assertEqual(
                    expected_lines,
                    lines_read,
                    msg="Test with {0} of new line {1} followed by {2} of {3}".format(number_of_new_lines, repr(new_line),
                                                                                  chunk_size, repr(s)))
                os.unlink(t.name)

    def test_file_with_new_lines_and_some_accented_characters_in_chunk_size(self):
        """Test a file with many new lines and a random text of size custom chunk_size."""
        chunk_size = 3
        b = b'\xc3\xa9'
        s = b.decode("utf-8")
        for number_of_new_lines in xrange(21):
            for new_line in new_lines:  # test with variety of new lines
                with tempfile.NamedTemporaryFile(delete=False) as t:
                    TestFileReadBackwards.write(t, new_line * number_of_new_lines)
                    TestFileReadBackwards.write(t, s * chunk_size)
                f = FileReadBackwards(t.name, chunk_size=chunk_size)
                expected_lines = deque()
                for _ in xrange(number_of_new_lines):
                    expected_lines.append("")
                expected_lines.append(s * chunk_size)
                lines_read = deque()
                for l in f:
                    lines_read.appendleft(l)
                self.assertEqual(
                    expected_lines,
                    lines_read,
                    msg="Test with {0} of new line {1} followed by {2} of \\xc3\\xa9".format(number_of_new_lines,
                                                                                          repr(new_line), chunk_size))
                os.unlink(t.name)

    def test_unsupported_encoding(self):
        """Test when users pass in unsupported encoding, NotImplementedError should be thrown."""
        with tempfile.NamedTemporaryFile(delete=False) as t:
            pass
        with self.assertRaises(NotImplementedError):
            _ = FileReadBackwards(t.name, encoding="not-supported-encoding")  # noqa: F841
