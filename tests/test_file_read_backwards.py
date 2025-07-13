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


created_files = set()


def helper_write(t, s, encoding="utf-8"):
    """A helper method to write out string s in specified encoding."""
    t.write(s.encode(encoding))


def helper_create_temp_file(generator=None, encoding='utf-8'):
    global created_files
    if generator is None:
        generator = ("line {}!\n".format(i) for i in range(42))
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


class TestFileReadBackwardsReadline:
    """Test class focused specifically on the readline() functionality."""
    
    def test_readline_with_completely_empty_file(self, empty_file):
        """Test readline on completely empty file returns empty string."""
        with FileReadBackwards(empty_file.name) as f:
            line = f.readline()
            assert line == ""
            
            # Subsequent calls should also return empty string
            line = f.readline()
            assert line == ""

    def test_readline_with_single_newline_char_different_encodings(self):
        """Test readline with files containing only a newline character in different encodings."""
        for encoding, new_line in itertools.product(supported_encodings, new_lines):
            temp_file = helper_create_temp_file((line for line in [new_line]), encoding=encoding)
            with FileReadBackwards(temp_file.name, encoding=encoding) as f:
                line = f.readline()
                expected_line = "" + os.linesep
                assert line == expected_line
                
                # Next readline should return empty string
                line = f.readline()
                assert line == ""

    def test_readline_with_single_line_text_and_newline(self):
        """Test readline with a single line of text followed by newline."""
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

    def test_readline_with_two_lines_of_text(self):
        """Test readline with two lines of text - should read in reverse order."""
        line0 = "Line0"
        line1 = "Line1"
        for new_line in new_lines:
            line0_with_n = "{}{}".format(line0, new_line)
            line1_with_n = "{}{}".format(line1, new_line)
            temp_file = helper_create_temp_file((line for line in [line0_with_n, line1_with_n]))
            with FileReadBackwards(temp_file.name) as fp:
                # First readline should return the last line (Line1)
                line = fp.readline()
                expected_line = line1 + os.linesep
                assert line == expected_line

                # Second readline should return the first line (Line0)
                second_line = fp.readline()
                expected_second_line = line0 + os.linesep
                assert second_line == expected_second_line

                # Third readline should return empty string
                third_line = fp.readline()
                expected_third_line = ""
                assert third_line == expected_third_line

    def test_readline_with_multiple_lines(self):
        """Test readline with multiple lines to ensure proper reverse order."""
        lines = ["First line", "Second line", "Third line", "Fourth line"]
        for new_line in new_lines:
            lines_with_newline = [line + new_line for line in lines]
            temp_file = helper_create_temp_file((line for line in lines_with_newline))
            with FileReadBackwards(temp_file.name) as fp:
                # Read all lines and verify they come in reverse order
                read_lines = []
                while True:
                    line = fp.readline()
                    if line == "":
                        break
                    # Remove the os.linesep that readline() adds
                    clean_line = line.rstrip(os.linesep)
                    read_lines.append(clean_line)
                
                # Should read lines in reverse order
                expected_order = list(reversed(lines))
                assert read_lines == expected_order

    def test_readline_with_accented_characters(self):
        """Test readline with accented characters in different encodings."""
        b = b'Caf\xc3\xa9'  # accented e in utf-8
        s = b.decode("utf-8")
        for encoding in supported_encodings:
            if encoding == "utf-8":  # Only test with UTF-8 for accented chars
                for new_line in new_lines:
                    temp_file = helper_create_temp_file((line for line in [s, new_line]), encoding=encoding)
                    with FileReadBackwards(temp_file.name, encoding=encoding) as f:
                        line = f.readline()
                        expected_line = s + os.linesep
                        assert line == expected_line

    def test_readline_with_varying_chunk_sizes(self):
        """Test readline with different chunk sizes to ensure it works regardless of buffer size."""
        test_lines = ["Short", "A much longer line with more content", "Medium length line"]
        chunk_sizes = [1, 3, 8, 16, 64]
        
        for chunk_size in chunk_sizes:
            for new_line in new_lines:
                lines_with_newline = [line + new_line for line in test_lines]
                temp_file = helper_create_temp_file((line for line in lines_with_newline))
                with FileReadBackwards(temp_file.name, chunk_size=chunk_size) as fp:
                    read_lines = []
                    while True:
                        line = fp.readline()
                        if line == "":
                            break
                        clean_line = line.rstrip(os.linesep)
                        read_lines.append(clean_line)
                    
                    expected_order = list(reversed(test_lines))
                    assert read_lines == expected_order

    def test_readline_with_empty_lines(self):
        """Test readline with files containing empty lines."""
        for new_line in new_lines:
            # Create file with: line1, empty line, line2, empty line
            content = ["Line1", new_line, "", new_line, "Line2", new_line, "", new_line]
            temp_file = helper_create_temp_file((line for line in content))
            with FileReadBackwards(temp_file.name) as fp:
                # Should read in reverse: empty, Line2, empty, Line1
                line1 = fp.readline().rstrip(os.linesep)
                assert line1 == ""
                
                line2 = fp.readline().rstrip(os.linesep)
                assert line2 == "Line2"
                
                line3 = fp.readline().rstrip(os.linesep)
                assert line3 == ""
                
                line4 = fp.readline().rstrip(os.linesep)
                assert line4 == "Line1"
                
                # Should be at end
                line5 = fp.readline()
                assert line5 == ""

    def test_readline_with_file_without_final_newline(self):
        """Test readline with file that doesn't end with a newline."""
        content = "Line without newline"
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
        temp_file.write(content)
        temp_file.close()
        created_files.add(temp_file)
        
        with FileReadBackwards(temp_file.name) as fp:
            line = fp.readline()
            expected_line = content + os.linesep
            assert line == expected_line
            
            # Next call should return empty
            line = fp.readline()
            assert line == ""

    def test_unsupported_encoding_raises_error(self, empty_file):
        """Test that unsupported encoding raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            _ = FileReadBackwards(empty_file.name, encoding="not-supported-encoding")


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
