import pytest

from mocktrics_exporter.valueModels import parse_size


def test_parse_int():
    assert parse_size(0) == 0.0
    assert parse_size(10) == 10.0
    assert parse_size(-10) == -10.0


def test_parse_float():
    assert parse_size(0.0) == 0.0
    assert parse_size(10.0) == 10.0
    assert parse_size(-10.0) == -10.0


def test_parse_string():
    assert parse_size("2u") == 1e-6 * 2
    assert parse_size("2m") == 1e-3 * 2
    assert parse_size("2k") == 1e3 * 2
    assert parse_size("2M") == 1e6 * 2
    assert parse_size("2G") == 1e9 * 2


def test_parse_string_no_match():

    with pytest.raises(ValueError):
        parse_size("2")

    with pytest.raises(ValueError):
        parse_size("2.0")

    with pytest.raises(ValueError):
        parse_size("2h")

    with pytest.raises(ValueError):
        parse_size("k2")
