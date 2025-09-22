import random

import pydantic
import pytest

from mocktrics_exporter.valueModels import GaussianValue


def test_gaussian_value(monkeypatch):

    monkeypatch.setattr(random, "gauss", lambda mean, sigma: 100.0)
    gaussian_value = GaussianValue(mean=0, sigma=1.0, labels=[""])

    assert gaussian_value.get_value() == 100.0


@pytest.mark.parametrize(
    "labels",
    [
        ([]),
        ([""]),
        (["test"]),
        (["test1", "test2"]),
    ],
)
def test_gaussian_value_labels(labels):
    gaussian_value = GaussianValue(mean=0, sigma=1.0, labels=labels)
    assert labels == gaussian_value.labels


def test_static_value_kind():
    GaussianValue(mean=0, sigma=1.0, labels=[], kind="gaussian")
    with pytest.raises(pydantic.ValidationError):
        GaussianValue(mean=0, sigma=1.0, labels=[], kind="test")  # type: ignore[arg-type]
