# tests/test_rules/test_m4_rules.py


def test_number_after_noun_placeholder():
    from src.rules.np.m4.number_after_noun_rule import NumberAfterNounRule
    r = NumberAfterNounRule()
    assert r.target_label == "m4"
