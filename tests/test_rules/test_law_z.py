# tests/test_rules/test_law_z.py
"""تست‌های قانون ض (LawZRule) — از برنچ genspark."""
import pytest

from src.ht_token import Token
from src.core.context import Context
from src.rules.np.special.law_z import LawZRule, DEFAULT_PLURAL_HEADS

VAGUE = {"large", "huge", "great", "various", "enormous", "vast"}


def _ctx(**kwargs):
    c = Context()
    c.vague_quant_set = set(VAGUE)
    try:
        from nltk.corpus import wordnet as wn
        wn.synsets("dog")
        c.wn = wn
    except Exception:
        c.wn = None
    for k, v in kwargs.items():
        setattr(c, k, v)
    return c


def _toks(*pairs):
    return [Token(w, lbl, "", index=i) for i, (w, lbl) in enumerate(pairs)]


def _words(tokens):
    return [t.word for t in tokens]


def test_metadata():
    r = LawZRule()
    assert r.name == "law_z"
    assert r.target_label == "special"
    assert r.priority == 81
    assert "numbers" in DEFAULT_PLURAL_HEADS


def test_merge_vague_plus_head_of():
    tokens = _toks(("large", ""), ("numbers", ""), ("of", ""), ("people", ""))
    changed = LawZRule().apply(tokens, _ctx())
    assert changed is True
    assert _words(tokens) == ["large numbers of", "people"]
    assert tokens[0].label == "m1"


def test_merge_with_m2_and_adv_modifiers():
    tokens = _toks(
        ("really", "adv"), ("big", "m2"), ("piles", ""),
        ("of", ""), ("paper", ""),
    )
    assert LawZRule().apply(tokens, _ctx()) is True
    assert _words(tokens) == ["really big piles of", "paper"]


def test_merge_vague_labelled_as_m1_is_allowed():
    tokens = _toks(("huge", "m1"), ("amounts", ""), ("of", ""), ("money", ""))
    assert LawZRule().apply(tokens, _ctx()) is True
    assert _words(tokens) == ["huge amounts of", "money"]


def test_merge_two_occurrences_in_sentence():
    tokens = _toks(
        ("large", ""), ("numbers", ""), ("of", ""), ("cats", ""),
        (",", ""), ("huge", ""), ("piles", ""), ("of", ""), ("dogs", ""),
    )
    assert LawZRule().apply(tokens, _ctx()) is True
    assert _words(tokens) == [
        "large numbers of", "cats", ",", "huge piles of", "dogs"
    ]


def test_custom_plural_head_via_ctx_extra():
    ctx = _ctx()
    ctx.extra["law_z_plural_heads"] = {"stacks"}
    tokens = _toks(("large", ""), ("stacks", ""), ("of", ""), ("books", ""))
    assert LawZRule().apply(tokens, ctx) is True
    assert _words(tokens)[0] == "large stacks of"


def test_no_merge_without_modifier():
    tokens = _toks(("numbers", ""), ("of", ""), ("people", ""))
    assert LawZRule().apply(tokens, _ctx()) is False


def test_no_merge_when_head_not_plural():
    tokens = _toks(("large", ""), ("number", ""), ("of", ""), ("people", ""))
    assert LawZRule().apply(tokens, _ctx()) is False


def test_no_merge_without_of():
    tokens = _toks(("large", ""), ("numbers", ""), ("came", ""))
    assert LawZRule().apply(tokens, _ctx()) is False


def test_possessive_pronoun_in_np_blocks_rule():
    tokens = _toks(
        ("his", "m3"), ("large", ""), ("numbers", ""),
        ("of", ""), ("friends", ""),
    )
    assert LawZRule().apply(tokens, _ctx()) is False


def test_possessive_s_in_np_blocks_rule():
    tokens = _toks(
        ("John", ""), ("'s", ""), ("huge", ""), ("piles", ""),
        ("of", ""), ("books", ""),
    )
    assert LawZRule().apply(tokens, _ctx()) is False


def test_possessive_in_previous_np_does_not_block():
    tokens = _toks(
        ("my", "m3"), ("dog", ""), (",", ""),
        ("large", ""), ("numbers", ""), ("of", ""), ("cats", ""),
    )
    assert LawZRule().apply(tokens, _ctx()) is True
    assert _words(tokens) == ["my", "dog", ",", "large numbers of", "cats"]


def test_real_m1_before_modifiers_blocks_merge():
    tokens = _toks(
        ("the", "m1"), ("large", ""), ("numbers", ""),
        ("of", ""), ("people", ""),
    )
    assert LawZRule().apply(tokens, _ctx()) is False


def test_numeric_m1_blocks_merge():
    tokens = [
        Token("two", "m1", "cardinal", index=0),
        Token("large", "", "", index=1),
        Token("groups", "", "", index=2),
        Token("of", "", "", index=3),
        Token("students", "", "", index=4),
    ]
    assert LawZRule().apply(tokens, _ctx()) is False


def test_locked_token_is_respected():
    tokens = _toks(("large", ""), ("numbers", ""), ("of", ""), ("people", ""))
    tokens[1].locked = True
    assert LawZRule().apply(tokens, _ctx()) is False


def test_no_crash_without_wordnet():
    ctx = _ctx()
    ctx.wn = None
    tokens = _toks(("large", ""), ("numbers", ""), ("of", ""), ("people", ""))
    assert LawZRule().apply(tokens, ctx) is True


def test_idempotent_second_pass():
    tokens = _toks(("large", ""), ("numbers", ""), ("of", ""), ("people", ""))
    rule = LawZRule()
    assert rule.apply(tokens, _ctx()) is True
    assert rule.apply(tokens, _ctx()) is False


def _has_wn():
    try:
        from nltk.corpus import wordnet as wn
        wn.synsets("dog")
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _has_wn(), reason="WordNet در دسترس نیست")
def test_wordnet_adjective_not_in_vague_set_is_modifier():
    ctx = _ctx()
    ctx.vague_quant_set = set()
    tokens = _toks(("different", ""), ("kinds", ""), ("of", ""), ("fruit", ""))
    assert LawZRule().apply(tokens, ctx) is True
    assert _words(tokens) == ["different kinds of", "fruit"]


@pytest.mark.skipif(not _has_wn(), reason="WordNet در دسترس نیست")
def test_verb_after_of_blocks_merge():
    tokens = _toks(("various", ""), ("kinds", ""), ("of", ""), ("eat", ""))
    assert LawZRule().apply(tokens, _ctx()) is False


@pytest.mark.skipif(not _has_wn(), reason="WordNet در دسترس نیست")
def test_head_amounts_not_treated_as_np_boundary():
    tokens = _toks(
        ("huge", ""), ("amounts", ""), ("of", ""), ("his", "m3"),
        ("money", ""),
    )
    assert LawZRule().apply(tokens, _ctx()) is False
