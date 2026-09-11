# tests/test_rules/test_m5_rules.py


def test_fallback_placeholder():
    from src.rules.np.m5.fallback_rule import FallbackRule
    r = FallbackRule()
    assert r.target_label == "m5"
