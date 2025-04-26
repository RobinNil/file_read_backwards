#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `buffer_work_space` module."""

import io
import os
import tempfile
import pytest
from pytest_mock import MockerFixture
from file_read_backwards.buffer_work_space import BufferWorkSpace
from file_read_backwards.buffer_work_space import new_lines_bytes
from file_read_backwards.buffer_work_space import _find_furthest_new_line
from file_read_backwards.buffer_work_space import _remove_trailing_new_line
from file_read_backwards.buffer_work_space import _get_file_size
from file_read_backwards.buffer_work_space import _is_partially_read_new_line
from file_read_backwards.buffer_work_space import _get_what_to_read_next
from file_read_backwards.buffer_work_space import _get_next_chunk


class TestFindFurthestNewLine:
    def test_find_furthest_new_line_with_no_new_line_in_empty_byte_string(self):
        test_string = b""
        r = _find_furthest_new_line(test_string)
        assert r == -1

    def test_find_furthest_new_line_with_no_new_line_in_non_empty_byte_string(self):
        test_string = b"SomeRandomCharacters"
        r = _find_furthest_new_line(test_string)
        assert r == -1

    def test_find_furthest_new_line_with_bytestring_with_new_line_at_the_end(self):
        base_string = b"SomeRandomCharacters"
        for n in new_lines_bytes:
            test_string = base_string + n
            expected_value = len(test_string) - 1
            r = _find_furthest_new_line(test_string)
            assert r == expected_value

    def test_find_furthest_new_line_with_bytestring_with_new_line_in_the_middle(self):
        base_string = b"SomeRandomCharacters"
        for n in new_lines_bytes:
            test_string = base_string + n + base_string
            expected_value = len(base_string) + len(n) - 1
            r = _find_furthest_new_line(test_string)
            assert r == expected_value

    def test_find_furthest_new_line_with_bytestring_with_new_line_in_the_middle_and_end(self):
        base_string = b"SomeRandomCharacters"
        for n in new_lines_bytes:
            test_string = base_string + n + base_string + n
            expected_value = len(test_string) - 1
            r = _find_furthest_new_line(test_string)
            assert r == expected_value


class TestRemoveTrailingNewLine:
    def test_remove_trailing_new_line_with_empty_byte_string(self):
        test_string = b""
        expected_string = test_string
        r = _remove_trailing_new_line(test_string)
        assert r == expected_string

    def test_remove_trailing_new_line_with_non_empty_byte_string_with_no_new_line(self):
        test_string = b"Something"
        expected_string = test_string
        r = _remove_trailing_new_line(test_string)
        assert r == expected_string

    def test_remove_trailing_new_line_with_non_empty_byte_string_with_variety_of_new_lines(self):
        expected_str = b"Something"
        for n in new_lines_bytes:
            test_string = expected_str + n
            r = _remove_trailing_new_line(test_string)
            assert r == expected_str

    def test_remove_trailing_new_line_with_non_empty_byte_string_with_variety_of_new_lines_in_the_middle(self):
        base_string = b"Something"
        for n in new_lines_bytes:
            test_string = base_string + n + base_string
            expected_string = test_string
            r = _remove_trailing_new_line(test_string)
            assert r == expected_string


class TestGetFileSize:
    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as t:
            pass
        expected_value = 0
        with io.open(t.name, mode="rb") as fp:
            r = _get_file_size(fp)
            assert r == expected_value
        os.unlink(t.name)

    def test_file_with_eight_bytes(self):
        with tempfile.NamedTemporaryFile(delete=False) as t:
            t.write(b"a" * 8)
        expected_value = 8
        with io.open(t.name, mode="rb") as fp:
            r = _get_file_size(fp)
            assert r == expected_value
        os.unlink(t.name)


class TestIsPartiallyReadNewLine:
    def test_when_we_have_a_partially_read_new_line(self):
        for n in new_lines_bytes:
            if len(n) > 1:
                b = n[-1]
                r = _is_partially_read_new_line(b)
                assert r


class TestGetWhatToReadNext:
    def test_with_empty_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as t:
            pass
        expected_result = (0, 0)
        with io.open(t.name, mode="rb") as fp:
            r = _get_what_to_read_next(fp, previously_read_position=0, chunk_size=3)
            assert r == expected_result
        os.unlink(t.name)

    def test_with_file_with_seven_bytes_of_alphanumeric(self):
        with tempfile.NamedTemporaryFile(delete=False) as t:
            t.write(b"abcdefg")
        expected_result = (4, 3)
        with io.open(t.name, mode="rb") as fp:
            r = _get_what_to_read_next(fp, previously_read_position=7, chunk_size=3)
            assert r == expected_result
        os.unlink(t.name)

    def test_with_file_with_single_new_line(self):
        for n in new_lines_bytes:
            with tempfile.NamedTemporaryFile(delete=False) as t:
                t.write(n)
            expected_result = (0, len(n))
            chunk_size = len(n) + 1
            with io.open(t.name, mode="rb") as fp:
                r = _get_what_to_read_next(fp, previously_read_position=len(n), chunk_size=chunk_size)
                assert r == expected_result
            os.unlink(t.name)

    def test_with_file_where_we_need_to_read_more_than_chunk_size(self):
        with tempfile.NamedTemporaryFile(delete=False) as t:
            t.write(b"abcd\nfg")
        expected_result = (3, 4)
        with io.open(t.name, mode="rb") as fp:
            r = _get_what_to_read_next(fp, previously_read_position=7, chunk_size=3)
            assert r == expected_result
        os.unlink(t.name)


class TestGetNextChunk:
    def test_with_empty_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as t:
            pass
        expected_result = (b"", 0)
        with io.open(t.name, mode="rb") as fp:
            r = _get_next_chunk(fp, previously_read_position=0, chunk_size=3)
            assert r == expected_result
        os.unlink(t.name)

    def test_with_non_empty_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as t:
            t.write(b"abcdefg")
        expected_result = (b"efg", 4)
        with io.open(t.name, mode="rb") as fp:
            r = _get_next_chunk(fp, previously_read_position=7, chunk_size=3)
            assert r == expected_result
        os.unlink(t.name)

    def test_with_non_empty_file_where_we_read_more_than_chunk_size(self):
        with tempfile.NamedTemporaryFile(delete=False) as t:
            t.write(b"abcd\nfg")
        expected_result = (b"d\nfg", 3)
        with io.open(t.name, mode="rb") as fp:
            r = _get_next_chunk(fp, previously_read_position=7, chunk_size=3)
            assert r == expected_result
        os.unlink(t.name)


class TestBufferWorkSpace:
    def test_add_to_empty_buffer_work_space(self, mocker: MockerFixture):
        _get_file_size_mock = mocker.patch("file_read_backwards.buffer_work_space._get_file_size")
        fp_mock = mocker.Mock()
        _get_file_size_mock.return_value = 1024
        b = BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
        b.add_to_buffer(content=b"aaa", read_position=1021)
        assert b.read_buffer == b"aaa"
        assert b.read_position == 1021

    def test_add_to_non_empty_buffer_work_space(self, mocker: MockerFixture):
        _get_file_size_mock = mocker.patch("file_read_backwards.buffer_work_space._get_file_size")
        fp_mock = mocker.Mock()
        _get_file_size_mock.return_value = 1024
        b = BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
        b.add_to_buffer(content=b"aaa", read_position=1021)
        b.add_to_buffer(content=b"bbb", read_position=1018)
        assert b.read_buffer == b"bbbaaa"
        assert b.read_position == 1018

    def test_yieldable_for_new_initialized_buffer_work_space(self):
        with tempfile.NamedTemporaryFile(delete=False) as t:
            with io.open(t.name, mode="rb") as fp:
                b = BufferWorkSpace(fp, chunk_size=io.DEFAULT_BUFFER_SIZE)
                r = b.yieldable()
                assert not r
        os.unlink(t.name)

    def test_yieldable_for_unexhausted_buffer_space_with_single_new_line(self, mocker: MockerFixture):
        _get_file_size_mock = mocker.patch("file_read_backwards.buffer_work_space._get_file_size")
        fp_mock = mocker.Mock()
        _get_file_size_mock.return_value = 1024

        for n in new_lines_bytes:
            b = BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
            b.read_position = 1024 - len(n)
            b.read_buffer = n
            expected_result = False
            r = b.yieldable()
            assert r == expected_result

    def test_yieldable_for_buffer_space_with_two_new_lines(self, mocker: MockerFixture):
        _get_file_size_mock = mocker.patch("file_read_backwards.buffer_work_space._get_file_size")
        fp_mock = mocker.Mock()
        _get_file_size_mock.return_value = 1024

        for n in new_lines_bytes:
            b = BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
            b.read_position = 1024 - (len(n) * 2)
            b.read_buffer = n * 2
            expected_result = True
            r = b.yieldable()
            assert r == expected_result

    def test_yieldable_for_fully_read_with_unreturned_contents_in_buffer_space(self, mocker: MockerFixture):
        _get_file_size_mock = mocker.patch("file_read_backwards.buffer_work_space._get_file_size")
        fp_mock = mocker.Mock()
        _get_file_size_mock.return_value = 1024

        for n in new_lines_bytes:
            b = BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
            b.read_position = 0
            b.read_buffer = b""
            expected_result = True
            r = b.yieldable()
            assert r == expected_result

    def test_yieldable_for_fully_read_and_returned_contents_in_buffer_space(self, mocker: MockerFixture):
        _get_file_size_mock = mocker.patch("file_read_backwards.buffer_work_space._get_file_size")
        fp_mock = mocker.Mock()
        _get_file_size_mock.return_value = 1024

        for n in new_lines_bytes:
            b = BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
            b.read_position = 0
            b.read_buffer = None
            r = b.yieldable()
            assert not r

    def test_return_line_with_buffer_space_with_two_new_lines(self, mocker: MockerFixture):
        _get_file_size_mock = mocker.patch("file_read_backwards.buffer_work_space._get_file_size")
        fp_mock = mocker.Mock()
        _get_file_size_mock.return_value = 1024

        for n in new_lines_bytes:
            b = BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
            b.read_position = 1024 - (len(n) * 2)
            b.read_buffer = n * 2
            expected_result = b""
            r = b.return_line()
            assert r == expected_result

    def test_return_line_with_buffer_space_with_some_contents_between_two_new_lines(self, mocker: MockerFixture):
        _get_file_size_mock = mocker.patch("file_read_backwards.buffer_work_space._get_file_size")
        fp_mock = mocker.Mock()
        _get_file_size_mock.return_value = 1024

        for n in new_lines_bytes:
            b = BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
            b.read_position = 1024 - (len(n) * 2)
            b.read_buffer = n + b"Something" + n
            expected_result = b"Something"
            r = b.return_line()
            assert r == expected_result

    def test_return_line_with_buffer_space_with_fully_read_in_contents_at_its_last_line(self, mocker: MockerFixture):
        _get_file_size_mock = mocker.patch("file_read_backwards.buffer_work_space._get_file_size")
        fp_mock = mocker.Mock()
        _get_file_size_mock.return_value = 1024

        for n in new_lines_bytes:
            b = BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
            b.read_position = 0
            b.read_buffer = b"LastLineYay"
            expected_result = b"LastLineYay"
            r = b.return_line()
            assert r == expected_result

    def test_return_line_contract_violation(self, mocker: MockerFixture):
        _get_file_size_mock = mocker.patch("file_read_backwards.buffer_work_space._get_file_size")
        fp_mock = mocker.Mock()
        _get_file_size_mock.return_value = 0

        b = BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
        with pytest.raises(AssertionError):
            b.return_line()

    def test_has_returned_every_line_empty_file(self, mocker: MockerFixture):
        _get_file_size_mock = mocker.patch("file_read_backwards.buffer_work_space._get_file_size")
        fp_mock = mocker.Mock()
        _get_file_size_mock.return_value = 0

        b = BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
        r = b.has_returned_every_line()
        assert r

    def test_has_returned_every_line_with_not_fully_read_in_buffer_space(self, mocker: MockerFixture):
        _get_file_size_mock = mocker.patch("file_read_backwards.buffer_work_space._get_file_size")
        fp_mock = mocker.Mock()
        _get_file_size_mock.return_value = 1024

        b = BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
        b.read_position = 1
        r = b.has_returned_every_line()
        assert not r

    def test_has_returned_every_line_with_fully_read_in_and_unprocessed_buffer_space(self, mocker: MockerFixture):
        _get_file_size_mock = mocker.patch("file_read_backwards.buffer_work_space._get_file_size")
        fp_mock = mocker.Mock()
        _get_file_size_mock.return_value = 1024

        b = BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
        b.read_position = 0
        b.read_buffer = b"abc"
        r = b.has_returned_every_line()
        assert not r

    def test_has_returned_every_line_with_fully_read_in_and_processed_buffer_space(self, mocker: MockerFixture):
        _get_file_size_mock = mocker.patch("file_read_backwards.buffer_work_space._get_file_size")
        fp_mock = mocker.Mock()
        _get_file_size_mock.return_value = 1024

        b = BufferWorkSpace(fp_mock, chunk_size=io.DEFAULT_BUFFER_SIZE)
        b.read_position = 0
        b.read_buffer = None
        r = b.has_returned_every_line()
        assert r
