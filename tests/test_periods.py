import pytest

from lakehouse_gov.periods import PeriodParseError, parse_period, to_label


def test_reference_period_maps_to_september_2026():
    p = parse_period("Y14 M9")
    assert (p.year, p.month, p.key) == (2026, 9, 202609)
    assert p.label == "Y14 M9"  # original label retained


@pytest.mark.parametrize("label", ["y14 m9", " Y14M9 ", "Y14  M9"])
def test_tolerant_to_case_and_spacing(label):
    assert parse_period(label).key == 202609


@pytest.mark.parametrize("label", ["September 2026", "Y14 M13", "Y14 M0", "", "2026-09"])
def test_bad_labels_are_surfaced_not_coerced(label):
    with pytest.raises(PeriodParseError):
        parse_period(label)


def test_none_label():
    with pytest.raises(PeriodParseError):
        parse_period(None)


def test_round_trip():
    for y in (2025, 2026):
        for m in range(1, 13):
            assert parse_period(to_label(y, m)).key == y * 100 + m
