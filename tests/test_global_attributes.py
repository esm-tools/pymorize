import pytest
from pymorize.global_attributes import parse_variant_label, update_variant_label
import pymorize.global_attributes as ga


simple_cases = [
    # (label, expected)
    (
        "r1i2p3f4",
        {
            "realization_index": 1,
            "initialization_index": 2,
            "physics_index": 3,
            "forcing_index": 4,
        },
    ),
    (
        "r10i20p30f40",
        {
            "realization_index": 10,
            "initialization_index": 20,
            "physics_index": 30,
            "forcing_index": 40,
        },
    ),
    (
        "r0i0p0f0",
        {
            "realization_index": 0,
            "initialization_index": 0,
            "physics_index": 0,
            "forcing_index": 0,
        },
    ),
]


@pytest.mark.parametrize("label, expected", simple_cases)
def test_parse_variant_label_realistic_labels(label, expected):
    result = parse_variant_label(label)
    assert result == expected, f"Failed Test ID: {label}"


edge_cases = [
    (
        "r01i02p03f04",
        {
            "realization_index": 1,
            "initialization_index": 2,
            "physics_index": 3,
            "forcing_index": 4,
        },
    ),
    (
        "r001i0002p0003f0004",
        {
            "realization_index": 1,
            "initialization_index": 2,
            "physics_index": 3,
            "forcing_index": 4,
        },
    ),
]


@pytest.mark.parametrize("label, expected", edge_cases)
def test_parse_variant_label_edge_cases(label, expected):
    result = parse_variant_label(label)
    assert result == expected, f"Failed Test ID: {label}"


error_cases = [
    ("r1i2p3", pytest.raises(ValueError)),
    ("r1i2p3f", pytest.raises(ValueError)),
    ("1i2p3f4", pytest.raises(ValueError)),
    ("r1i2p3f4x", pytest.raises(ValueError)),
    ("", pytest.raises(ValueError)),
    (None, pytest.raises(ValueError)),
    # negitive indices not supported. should they be?
    ("r-1i-2p-3f-4", pytest.raises(ValueError)),
    # strict match, no trailing extra characters
    ("r1i2p3f4a0b1", pytest.raises(ValueError)),
    # strict match, no leading extra characters
    ("c2d2r1i2p3f4", pytest.raises(ValueError)),
    # strict match, no leading or trailing extra characters
    ("c2d2r1i2p3f4a0b1", pytest.raises(ValueError)),
    # no spaces
    ("r1 i2 p3 f4", pytest.raises(ValueError)),
    ("r 1 i 2 p 3 f 4", pytest.raises(ValueError)),
]


@pytest.mark.parametrize("label, exception", error_cases)
def test_parse_variant_label_error_cases(label, exception):
    with exception:
        parse_variant_label(label)


def test_update_variant_label_adds_label_to_gattrs():
    label = "r10i20p30f40"
    d = {}
    update_variant_label(label=label, gattrs=d)
    assert label == d["variant_label"]


def test_update_variant_label_overrides_existing_label():
    label = "r10i20p30f40"
    d = {
        "realization_index": 1,
        "initialization_index": 2,
        "physics_index": 3,
        "forcing_index": 4,
        "variant_label": "r1i2p3f4",
    }
    update_variant_label(label=label, gattrs=d)
    assert d["variant_label"] == label
    assert d["realization_index"] == 10
    assert d["initialization_index"] == 20
    assert d["physics_index"] == 30
    assert d["forcing_index"] == 40


def test_update_license_with_no_extra_arguments():
    cv = {
        "institution_id": {"AWI": "AWI"},
        "license": {
            "license": "CMI6 model <Institution> under license <CC; license_id> License (<insert matching license>). further_info_url [and at <maintained by modeling group>]. yata yata yata.",
            "license_options": {
                "CC BY-SA 4.0": {
                    "license_id": "Creative Common",
                    "license_url": "https://cc.org",
                }
            },
        },
    }
    d = {}
    ga.update_license(d, cv)
    assert "license" in d
    assert "Creative Common" in d["license"]
    assert "AWI" in d["license"]
