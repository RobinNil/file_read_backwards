#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `file_read_backwards` module."""

import io
import itertools
import os
import tempfile
import unittest

from collections import deque
from mock import Mock, patch

from file_read_backwards.file_read_backwards import FileReadBackwards
from file_read_backwards.file_read_backwards import _BufferWorkSpace
from file_read_backwards.file_read_backwards import new_lines, new_lines_bytes
from file_read_backwards.file_read_backwards import _find_furthest_new_line
from file_read_backwards.file_read_backwards import _remove_trailing_new_line
from file_read_backwards.file_read_backwards import _get_file_size
from file_read_backwards.file_read_backwards import _is_partially_read_new_line
from file_read_backwards.file_read_backwards import _get_what_to_read_next
from file_read_backwards.file_read_backwards import _get_next_chunk
from file_read_backwards.file_read_backwards import supported_encodings

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
                msg="Test with {} encoding with {} as newline".format(encoding, repr(new_line)))
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
            self.assertEqual(expected_lines, lines_read, msg="Test with {} as newline".format(repr(new_line)))
            os.unlink(t.name)

    def test_file_with_one_line_of_text_followed_by_a_new_line_with_different_encodings(self):
        """Test a file with just one line of text followed by a new line."""
        for encoding, new_line in itertools.product(supported_encodings, new_lines):
            with tempfile.NamedTemporaryFile(delete=False) as t:
                TestFileReadBackwards.write(t, "something{}".format(new_line), encoding)
            f = FileReadBackwards(t.name)
            expected_lines = deque(["something"])
            lines_read = deque()
            for l in f:
                lines_read.appendleft(l)
            self.assertEqual(
                expected_lines,
                lines_read,
                msg="Test with {} encoding with {} as newline".format(encoding, repr(new_line)))
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
                    msg="Test with {} of new line {} followed by {} of {}".format(number_of_new_lines, repr(new_line),
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
                    msg="Test with {} of new line {} followed by {} of \\xc3\\xa9".format(number_of_new_lines,
                                                                                          repr(new_line), chunk_size))
                os.unlink(t.name)

    def test_unsupported_encoding(self):
        """Test when users pass in unsupported encoding, NotImplementedError should be thrown."""
        with tempfile.NamedTemporaryFile(delete=False) as t:
            pass
        with self.assertRaises(NotImplementedError):
            _ = FileReadBackwards(t.name, encoding="not-supported-encoding")  # noqa: F841


class TestFindFurthestNewLine(unittest.TestCase):

    """Class that contains test cases for the _find_furthest_new_line module."""

    def setUp(self):  # noqa: N802
        pass

    def tearDown(self):  # noqa: N802
        pass

    def test_find_furthest_new_line_with_no_new_line_in_empty_byte_string(self):
        """Expect return value of -1 when empty bytestring is passed in."""
        test_string = b""
        r = _find_furthest_new_line(test_string)
        self.assertEqual(r, -1)

    def test_find_furthest_new_line_with_no_new_line_in_non_empty_byte_string(self):
        """Expect return value of -1 when non-empty bytestrings that don't contain new line is passed in."""
        test_string = b"SomeRandomCharacters"
        r = _find_furthest_new_line(test_string)
        self.assertEqual(r, -1)

    def test_find_furthest_new_line_with_bytestring_with_new_line_at_the_end(self):
        """Expect return value of the last index of the test_string because the new line is at the end."""
        base_string = b"SomeRandomCharacters"
        for n in new_lines_bytes:
            test_string = base_string + n
            expected_value = len(test_string) - 1
            r = _find_furthest_new_line(test_string)
            self.assertEqual(r, expected_value, msg="Test with {} as new line".format(repr(n)))

    def test_find_furthest_new_line_with_bytestring_with_new_line_in_the_middle(self):
        """Expect return value pointing to the middle of the test string where the newline is at."""
        base_string = b"SomeRandomCharacters"
        for n in new_lines_bytes:
            test_string = base_string + n + base_string
            expected_value = len(base_string) + len(n) - 1
            r = _find_furthest_new_line(test_string)
            self.assertEqual(r, expected_value, msg="Test with {} as new line".format(repr(n)))

    def test_find_furthest_new_line_with_bytestring_with_new_line_in_the_middle_and_end(self):
        """Expect return value of the last index of the test_string because the new line is at the end."""
        base_string = b"SomeRandomCharacters"
        for n in new_lines_bytes:
            test_string = base_string + n + base_string + n
            expected_value = len(test_string) - 1
            r = _find_furthest_new_line(test_string)
            self.assertEqual(r, expected_value, msg="Test with {} as new line".format(repr(n)))


class TestRemoveTrailingNewLine(unittest.TestCase):

    """Class that contains test cases for _remove_trailing_new_line."""

    def test_remove_trailing_new_line_with_empty_byte_string(self):
        """Expect nothing to change, because empty byte string does not contain trailing new line."""
        test_string = b""
        expected_string = test_string
        r = _remove_trailing_new_line(test_string)
        self.assertEqual(r, expected_string)

    def test_remove_trailing_new_line_with_non_empty_byte_string_with_no_new_line(self):
        """Expect nothing to change."""
        test_string = b"Something"
        expected_string = test_string
        r = _remove_trailing_new_line(test_string)
        self.assertEqual(r, expected_string)

    def test_remove_trailing_new_line_with_non_empty_byte_string_with_variety_of_new_lines(self):
        """Expect new lines to be removed at the end of the string."""
        expected_string = b"Something"
        for n in new_lines_bytes:
            test_string = expected_string + n
            r = _remove_trailing_new_line(test_string)
            self.assertEqual(
                r,
                expected_string,
                msg="Test with {} followed by {} as new line at the end of str".format(repr(expected_string), repr(n)))

    def test_remove_trailing_new_line_with_non_empty_byte_string_with_variety_of_new_lines_in_the_middle(self):
        """Expect nothing to change because the new line is in the middle."""
        base_string = b"Something"
        for n in new_lines_bytes:
            test_string = base_string + n + base_string
            expected_string = test_string
            r = _remove_trailing_new_line(test_string)
            self.assertEqual(r, expected_string, msg="Test with {} as new line".format(repr(n)))


class TestGetFileSize(unittest.TestCase):

    """Class that contains test cases for _get_file_size."""

    def test_empty_file(self):
        """Expect value of 0 because if it empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as t:
            pass
        expected_value = 0
        with io.open(t.name, mode="rb") as fp:
            r = _get_file_size(fp)
            self.assertEqual(r, expected_value)
        os.unlink(t.name)

    def test_file_with_eight_bytes(self):
        """Expect value of 8 because if it is an 8-bytes file."""
        with tempfile.NamedTemporaryFile(delete=False) as t:
            t.write(b"a" * 8)
        expected_value = 8
        with io.open(t.name, mode="rb") as fp:
            r = _get_file_size(fp)
            self.assertEqual(r, expected_value)
        os.unlink(t.name)


class TestIsPartiallyReadNewLine(unittest.TestCase):

    """Class that contains test cases for _is_partially_read_new_line."""

    def test_when_we_have_a_partially_read_new_line(self):
        """Insert bytestring that is the last byte of new line separator that is longer than 1 byte."""
        for n in new_lines_bytes:
            if len(n) > 1:
                b = n[-1]
                r = _is_partially_read_new_line(b)
                self.assertTrue(r)


class TestGetWhatToReadNext(unittest.TestCase):

    """Class that contains test cases for what to _get_what_to_read_next."""

    def test_with_empty_file(self):
        """Expect (0, 0) when we pass in empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as t:
            pass
        expected_result = (0, 0)
        with io.open(t.name, mode="rb") as fp:
            r = _get_what_to_read_next(fp, previously_read_position=0, chunk_size=3)
            self.assertEqual(expected_result, r)
        os.unlink(t.name)

    def test_with_file_with_seven_bytes_of_alphanumeric(self):
        """Test with alpha-numeric contents of size 7 bytes with chunk_size of 3. Expect (4, 3)."""
        with tempfile.NamedTemporaryFile(delete=False) as t:
            t.write(b"abcdefg")
        expected_result = (4, 3)
        with io.open(t.name, mode="rb") as fp:
            r = _get_what_to_read_next(fp, previously_read_position=7, chunk_size=3)
            self.assertEqual(expected_result, r)
        os.unlink(t.name)

    def test_with_file_with_single_new_line(self):
        """Test file with a single new line with variety of new_lines."""
        for n in new_lines_bytes:
            with tempfile.NamedTemporaryFile(delete=False) as t:
                t.write(n)
            expected_result = (0, len(n))
            chunk_size = len(n) + 1  # chunk size must be greater than len(n)
            with io.open(t.name, mode="rb") as fp:
                r = _get_what_to_read_next(fp, previously_read_position=len(n), chunk_size=chunk_size)
                self.assertEqual(r, expected_result)
            os.unlink(t.name)

    def test_with_file_where_we_need_to_read_more_than_chunk_size(self):
        """When we encounter character that may be part of a new line, we rewind further."""
        with tempfile.NamedTemporaryFile(delete=False) as t:
            t.write(b"abcd\nfg")
        expected_result = (3, 4)
        with io.open(t.name, mode="rb") as fp:
            r = _get_what_to_read_next(fp, previously_read_position=7, chunk_size=3)
            self.assertEqual(expected_result, r)
        os.unlink(t.name)


class TestGetNextChunk(unittest.TestCase):

    """Class that contains test cases for _get_next_chunk."""

    def test_with_empty_file(self):
        """Test with empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as t:
            pass
        expected_result = (b"", 0)
        with io.open(t.name, mode="rb") as fp:
            r = _get_next_chunk(fp, previously_read_position=0, chunk_size=3)
            self.assertEqual(r, expected_result)

    def test_with_non_empty_file(self):
        """Test with non-empty file where we are expected to read specified chunk size."""
        with tempfile.NamedTemporaryFile(delete=False) as t:
            t.write(b"abcdefg")
        expected_result = (b"efg", 4)
        with io.open(t.name, mode="rb") as fp:
            r = _get_next_chunk(fp, previously_read_position=7, chunk_size=3)
            self.assertEqual(expected_result, r)
        os.unlink(t.name)

    def test_with_non_empty_file_where_we_read_more_than_chunk_size(self):
        r"""Test with non-empty file where we are expected to read more than chunk size.

        Note: We read more than specified chunk size because we go further if we hit "\n".
        """
        with tempfile.NamedTemporaryFile(delete=False) as t:
            t.write(b"abcd\nfg")
        expected_result = (b"d\nfg", 3)
        with io.open(t.name, mode="rb") as fp:
            r = _get_next_chunk(fp, previously_read_position=7, chunk_size=3)
            self.assertEqual(expected_result, r)
        os.unlink(t.name)


class TestBufferWorkSpace(unittest.TestCase):

    """Class that contains test cases for _BufferWorkSpace."""

    def test_add_to_empty_buffer_work_space(self):
        """Test reading last 3 bytes from a 1024 byte file."""
        with patch("file_read_backwards.file_read_backwards._get_file_size") as _get_file_size_mock:
            fp_mock = Mock()
            _get_file_size_mock.return_value = 1024
            b = _BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
            b.add_to_buffer(content=b"aaa", read_position=1021)
            self.assertEqual(b.read_buffer, b"aaa")
            self.assertEqual(b.read_position, 1021)

    def test_add_to_non_empty_buffer_work_space(self):
        """Test adding to a non-empty buffer work space."""
        with patch("file_read_backwards.file_read_backwards._get_file_size") as _get_file_size_mock:
            fp_mock = Mock()
            _get_file_size_mock.return_value = 1024
            b = _BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
            b.add_to_buffer(content=b"aaa", read_position=1021)
            b.add_to_buffer(content=b"bbb", read_position=1018)
            self.assertEqual(b.read_buffer, b"bbbaaa")
            self.assertEqual(b.read_position, 1018)

    def test_yieldable_for_new_initialized_buffer_work_space(self):
        """Newly empty buffer work space should not be yieldable."""
        with tempfile.NamedTemporaryFile(delete=False) as t:
            with io.open(t.name, mode="rb") as fp:
                b = _BufferWorkSpace(fp, chunk_size=io.DEFAULT_BUFFER_SIZE)
                r = b.yieldable()
                self.assertFalse(r)

    def test_yieldable_for_unexhausted_buffer_space_with_single_new_line(self):
        """Buffer work space with a single new line (with read_position > 0) is not be yieldable."""
        with patch("file_read_backwards.file_read_backwards._get_file_size") as _get_file_size_mock:
            fp_mock = Mock()
            _get_file_size_mock.return_value = 1024

            for n in new_lines_bytes:
                b = _BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
                b.read_position = 1024 - len(n)
                b.read_buffer = n
                expected_result = False
                r = b.yieldable()
                self.assertEqual(r, expected_result)

    def test_yieldable_for_buffer_space_with_two_new_lines(self):
        """Buffer work space with a two new lines are yieldable."""
        with patch("file_read_backwards.file_read_backwards._get_file_size") as _get_file_size_mock:
            fp_mock = Mock()
            _get_file_size_mock.return_value = 1024

            for n in new_lines_bytes:
                b = _BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
                b.read_position = 1024 - (len(n) * 2)
                b.read_buffer = n * 2
                expected_result = True
                r = b.yieldable()
                self.assertEqual(r, expected_result)

    def test_yieldable_for_fully_read_with_unreturned_contents_in_buffer_space(self):
        """Buffer work space that has been fully read in and unreturned contents is yieldable.

        Note: fully read in and unreturned contents is represented by read_position = 0 and read_buffer is not None.
        """
        with patch("file_read_backwards.file_read_backwards._get_file_size") as _get_file_size_mock:
            fp_mock = Mock()
            _get_file_size_mock.return_value = 1024

            for n in new_lines_bytes:
                b = _BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
                b.read_position = 0
                b.read_buffer = b""
                expected_result = True
                r = b.yieldable()
                self.assertEqual(r, expected_result)

    def test_yieldable_for_fully_read_and_returned_contents_in_buffer_space(self):
        """_BufferWorkSpace that has been fully read in and returned contents is not yieldable.

        Note: fully read-in and returned is represented by read_position = 0, read_buffer is None.
        """
        with patch("file_read_backwards.file_read_backwards._get_file_size") as _get_file_size_mock:
            fp_mock = Mock()
            _get_file_size_mock.return_value = 1024

            for n in new_lines_bytes:
                b = _BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
                b.read_position = 0
                b.read_buffer = None
                r = b.yieldable()
                self.assertFalse(r)

    def test_return_line_with_buffer_space_with_two_new_lines(self):
        """With two new lines as its sole contents, the buffer space is expected to return b''."""
        with patch("file_read_backwards.file_read_backwards._get_file_size") as _get_file_size_mock:
            fp_mock = Mock()
            _get_file_size_mock.return_value = 1024

            for n in new_lines_bytes:
                b = _BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
                b.read_position = 1024 - (len(n) * 2)
                b.read_buffer = n * 2
                expected_result = b""
                r = b.return_line()
                self.assertEqual(r, expected_result)

    def test_return_line_with_buffer_space_with_some_contents_between_two_new_lines(self):
        """With some bytestrings in between 2 new lines, expect to have the bytestrings in the middle."""
        with patch("file_read_backwards.file_read_backwards._get_file_size") as _get_file_size_mock:
            fp_mock = Mock()
            _get_file_size_mock.return_value = 1024

            for n in new_lines_bytes:
                b = _BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
                b.read_position = 1024 - (len(n) * 2)
                b.read_buffer = n + b"Something" + n
                expected_result = b"Something"
                r = b.return_line()
                self.assertEqual(r, expected_result)

    def test_return_line_with_buffer_space_with_fully_read_in_contents_at_its_last_line(self):
        """With some bytestrings in between 2 new lines, expect to have the bytestrings in the middle."""
        with patch("file_read_backwards.file_read_backwards._get_file_size") as _get_file_size_mock:
            fp_mock = Mock()
            _get_file_size_mock.return_value = 1024

            for n in new_lines_bytes:
                b = _BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
                b.read_position = 0
                b.read_buffer = b"LastLineYay"
                expected_result = b"LastLineYay"
                r = b.return_line()
                self.assertEqual(r, expected_result)

    def test_return_line_contract_violation(self):
        """_BufferWorkSpace (of a completely empty file) would result in contract violation for return_line."""
        with patch("file_read_backwards.file_read_backwards._get_file_size") as _get_file_size_mock:
            fp_mock = Mock()
            _get_file_size_mock.return_value = 0

            b = _BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
            with self.assertRaises(AssertionError):
                b.return_line()

    def test_has_returned_every_line_empty_file(self):
        """With empty file (a degenerate case), it is expected to have returned everything."""
        with patch("file_read_backwards.file_read_backwards._get_file_size") as _get_file_size_mock:
            fp_mock = Mock()
            _get_file_size_mock.return_value = 0

            b = _BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
            r = b.has_returned_every_line()
            self.assertTrue(r)

    def test_has_returned_every_line_with_not_fully_read_in_buffer_space(self):
        """With BufferWorkSpace that has not fully read in, it definitely has not returned everything.

        Note that: not fully read in is represented by read_position != 0
        """
        with patch("file_read_backwards.file_read_backwards._get_file_size") as _get_file_size_mock:
            fp_mock = Mock()
            _get_file_size_mock.return_value = 1024

            b = _BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
            b.read_position = 1
            r = b.has_returned_every_line()
            self.assertFalse(r)

    def test_has_returned_every_line_with_fully_read_in_and_unprocessed_buffer_space(self):
        """BufferWorkSpace that has been fully read with some unprocessed buffer has not returned everything.

        Note: not fully read in and some unprocessed buffer is represented by read_position = 0 and read_buffer != None
        """
        with patch("file_read_backwards.file_read_backwards._get_file_size") as _get_file_size_mock:
            fp_mock = Mock()
            _get_file_size_mock.return_value = 1024

            b = _BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
            b.read_position = 0
            b.read_buffer = b"abc"
            r = b.has_returned_every_line()
            self.assertFalse(r)

    def test_has_returned_every_line_with_fully_read_in_and_processed_buffer_space(self):
        """_BufferWorkSpace that has been fully read in and fully processed has not returned everything.

        Note: not fully read in and some unprocessed buffer is represented by read_position = 0 and read_buffer = None
        """
        with patch("file_read_backwards.file_read_backwards._get_file_size") as _get_file_size_mock:
            fp_mock = Mock()
            _get_file_size_mock.return_value = 1024

            b = _BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
            b.read_position = 0
            b.read_buffer = None
            r = b.has_returned_every_line()
            self.assertTrue(r)
