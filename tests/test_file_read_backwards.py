#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `file_read_backwards` module."""

import itertools
import os
import tempfile
import pytest

from collections import deque

from file_read_backwards.file_read_backwards import FileReadBackwards
from file_read_backwards.file_read_backwards import supported_encodings
from file_read_backwards.buffer_work_space import new_lines


# doing this xrange/range dance so that we don't need to add additional dependencies of future or six modules
try:
    xrange
except NameError:
    xrange = range


created_files = set()


def helper_write(t, s, encoding="utf-8"):
    """A helper method to write out string s in specified encoding."""
    t.write(s.encode(encoding))


def helper_create_temp_file(generator=None, encoding='utf-8'):
    global created_files
    if generator is None:
        generator = ("line {}!\n".format(i) for i in xrange(42))
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    for line in generator:
        helper_write(temp_file, line, encoding)
    temp_file.close()
    print('Wrote file {}'.format(temp_file.name))
    created_files.add(temp_file)
    return temp_file


def helper_destroy_temp_file(temp_file):
    temp_file.close()
    os.unlink(temp_file.name)


def helper_destroy_temp_files():
    global created_files
    while created_files:
        helper_destroy_temp_file(created_files.pop())


@pytest.fixture(scope="module")
def empty_file():
    return helper_create_temp_file(generator=(_ for _ in []))


@pytest.fixture(scope="module")
def long_file():
    return helper_create_temp_file()


@pytest.fixture(scope="module", autouse=True)
def cleanup_files():
    yield
    helper_destroy_temp_files()


class TestFileReadBackwards:
    def test_with_completely_empty_file(self, empty_file):
        f = FileReadBackwards(empty_file.name)
        expected_lines = deque()
        lines_read = deque()
        for line in f:
            lines_read.appendleft(line)
        assert expected_lines == lines_read

    def test_file_with_a_single_new_line_char_with_different_encodings(self):
        for encoding, new_line in itertools.product(supported_encodings, new_lines):
            temp_file = helper_create_temp_file((line for line in [new_line]), encoding=encoding)
            f = FileReadBackwards(temp_file.name)
            expected_lines = deque([""])
            lines_read = deque()
            for line in f:
                lines_read.appendleft(line)
            assert expected_lines == lines_read

    def test_file_with_one_line_of_text_with_accented_char_followed_by_a_new_line(self):
        b = b'Caf\xc3\xa9'  # accented e in utf-8
        s = b.decode("utf-8")
        for new_line in new_lines:
            temp_file = helper_create_temp_file((line for line in [s, new_line]))
            f = FileReadBackwards(temp_file.name)
            expected_lines = deque([s])
            lines_read = deque()
            for line in f:
                lines_read.appendleft(s)
            assert expected_lines == lines_read

    def test_file_with_one_line_of_text_followed_by_a_new_line_with_different_encodings(self):
        for encoding, new_line in itertools.product(supported_encodings, new_lines):
            temp_file = helper_create_temp_file((line for line in ["something{0}".format(new_line)]), encoding=encoding)
            f = FileReadBackwards(temp_file.name)
            expected_lines = deque(["something"])
            lines_read = deque()
            for line in f:
                lines_read.appendleft(line)
            assert expected_lines == lines_read

    def test_file_with_varying_number_of_new_lines_and_some_text_in_chunk_size(self):
        chunk_size = 3
        s = "t"
        for number_of_new_lines in xrange(21):
            for new_line in new_lines:
                temp_file = helper_create_temp_file((line for line in [new_line * number_of_new_lines, s * chunk_size]))
                f = FileReadBackwards(temp_file.name, chunk_size=chunk_size)
                expected_lines = deque()
                for _ in xrange(number_of_new_lines):
                    expected_lines.append("")
                expected_lines.append(s * chunk_size)
                lines_read = deque()
                for line in f:
                    lines_read.appendleft(line)
                assert expected_lines == lines_read

    def test_file_with_new_lines_and_some_accented_characters_in_chunk_size(self):
        chunk_size = 3
        b = b'\xc3\xa9'
        s = b.decode("utf-8")
        for number_of_new_lines in xrange(21):
            for new_line in new_lines:
                temp_file = helper_create_temp_file((line for line in [new_line * number_of_new_lines, s * chunk_size]))
                f = FileReadBackwards(temp_file.name, chunk_size=chunk_size)
                expected_lines = deque()
                for _ in xrange(number_of_new_lines):
                    expected_lines.append("")
                expected_lines.append(s * chunk_size)
                lines_read = deque()
                for line in f:
                    lines_read.appendleft(line)
                assert expected_lines == lines_read

    def test_unsupported_encoding(self, empty_file):
        with pytest.raises(NotImplementedError):
            _ = FileReadBackwards(empty_file.name, encoding="not-supported-encoding")

    def test_file_with_one_line_of_text_readline(self):
        s = "Line0"
        for new_line in new_lines:
            temp_file = helper_create_temp_file((line for line in [s, new_line]))
            with FileReadBackwards(temp_file.name) as fp:
                line = fp.readline()
                expected_line = s + os.linesep
                assert line == expected_line

                second_line = fp.readline()
                expected_second_line = ""
                assert second_line == expected_second_line

    def test_file_with_two_lines_of_text_readline(self):
        line0 = "Line0"
        line1 = "Line1"
        for new_line in new_lines:
            line0_with_n = "{}{}".format(line0, new_line)
            line1_with_n = "{}{}".format(line1, new_line)
            temp_file = helper_create_temp_file((line for line in [line0_with_n, line1_with_n]))
            with FileReadBackwards(temp_file.name) as fp:
                line = fp.readline()
                expected_line = line1 + os.linesep
                assert line == expected_line

                second_line = fp.readline()
                expected_second_line = line0 + os.linesep
                assert second_line == expected_second_line

                third_line = fp.readline()
                expected_third_line = ""
                assert third_line == expected_third_line


class TestFileReadBackwardsAsContextManager:
    @pytest.fixture(scope="class", autouse=True)
    def temp_file(self):
        return helper_create_temp_file()

    def test_behaves_as_classic(self, temp_file):
        with FileReadBackwards(temp_file.name) as f:
            lines_read = deque()
            for line in f:
                lines_read.appendleft(line)
        f2 = FileReadBackwards(temp_file.name)
        lines_read2 = deque()
        for l2 in f2:
            lines_read2.appendleft(l2)
        assert lines_read == lines_read2


class TestFileReadBackwardsCloseFunctionality:
    @pytest.fixture(scope="class", autouse=True)
    def temp_file(self):
        return helper_create_temp_file()

    def test_close_on_iterator(self, temp_file):
        with FileReadBackwards(temp_file.name) as f:
            it = iter(f)
            for count, i in enumerate(it):
                if count == 2:
                    break
            assert not it.closed
            it.close()
            assert it.closed

    def test_not_creating_new_iterator(self, temp_file):
        with FileReadBackwards(temp_file.name) as f:
            it1 = iter(f)
            it2 = iter(f)
            assert it1 is it2

    def test_close_on_iterator_exhausted(self, temp_file):
        with FileReadBackwards(temp_file.name) as f:
            it = iter(f)
            for _ in it:
                pass
            assert it.closed

    def test_close_on_reader_exit(self, temp_file):
        with FileReadBackwards(temp_file.name) as f:
            it = iter(f)
        assert it.closed

    def test_close_on_reader_explicitly(self, temp_file):
        f = FileReadBackwards(temp_file.name)
        it = iter(f)
        assert not it.closed
        f.close()
        assert it.closed

    def test_close_on_reader_with_already_closed_iterator(self, temp_file):
        with FileReadBackwards(temp_file.name) as f:
            it = iter(f)
            it.close()
        assert it.closed

    def test_cannot_iterate_when_closed(self, temp_file):
        with FileReadBackwards(temp_file.name) as f:
            it = iter(f)
            it.close()
            for _ in it:
                pytest.fail("An iterator should be exhausted when closed.")
