# tests/test_rules/test_special_rules.py


def test_much_placeholder():
    from src.rules.np.special.much_rule import MuchRule
    r = MuchRule()
    assert r.target_label == "special"
