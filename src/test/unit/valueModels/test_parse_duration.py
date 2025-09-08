import pytest

from mocktrics_exporter.valueModels import parse_duration


def test_parse_int():
    assert parse_duration(0) == 0
    assert parse_duration(10) == 10


def test_parse_int_out_of_bounds():
    with pytest.raises(ValueError):
        parse_duration(-1)


def test_parse_string():
    assert parse_duration("2s") == 1 * 2
    assert parse_duration("2m") == 60 * 2
    assert parse_duration("2h") == 3600 * 2
    assert parse_duration("2d") == 86400 * 2


def test_parse_string_no_match():
    with pytest.raises(ValueError):
        parse_duration("2")

    with pytest.raises(ValueError):
        parse_duration("2k")

    with pytest.raises(ValueError):
        parse_duration("s2")
