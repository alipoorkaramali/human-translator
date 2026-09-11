# tests/test_rules/test_m3_rules.py
import pytest


def test_possessive_placeholder():
    from src.rules.np.m3.possessive_rule import PossessiveRule
    r = PossessiveRule()
    assert r.target_label == "m3"
