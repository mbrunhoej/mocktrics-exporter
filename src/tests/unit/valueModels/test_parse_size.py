import pytest

from mocktrics_exporter.valueModels import parse_size


@pytest.mark.parametrize(
    "value, result, should_raise",
    [
        (0, 0.0, None),
        (10, 10.0, None),
        (-10, -10.0, None),
        (0.0, 0.0, None),
        (10.0, 10.0, None),
        (-10.0, -10.0, None),
        ("2u", 1e-6 * 2, None),
        ("2m", 1e-3 * 2, None),
        ("2k", 1e3 * 2, None),
        ("2M", 1e6 * 2, None),
        ("2G", 1e9 * 2, None),
        ("2", None, ValueError),
        ("2.0", None, ValueError),
        ("2h", None, ValueError),
        ("k2", None, ValueError),
    ],
)
def test_parse_size(value, result, should_raise):
    if should_raise:
        with pytest.raises(should_raise):
            parse_size(value)
    else:
        assert parse_size(value) == result
