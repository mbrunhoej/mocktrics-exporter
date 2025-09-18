import pytest

from mocktrics_exporter.valueModels import parse_duration


@pytest.mark.parametrize(
    "value, result, should_raise",
    [
        (0, 0, None),
        (10, 10, None),
        (-1, None, ValueError),
        ("2s", 2, None),
        ("2m", 60 * 2, None),
        ("2h", 3600 * 2, None),
        ("2d", 86400 * 2, None),
        ("2", None, ValueError),
        ("2k", None, ValueError),
        ("s2", None, ValueError),
    ],
)
def test_parse_duration(value, result, should_raise):
    if should_raise:
        with pytest.raises(should_raise):
            parse_duration(value)
    else:
        assert parse_duration(value) == result
