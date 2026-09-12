# tests/test_utils.py
# تست‌های توابع کمکی src.utils
import pytest
from src.utils import (
    number_type, is_possessive_or_s, is_np_boundary,
    is_punctuation, is_and_word, syllable_count,
    is_cardinal_word, is_ordinal_word,
    preprocess_text, tokenize_english,
    possessive_before_index,
)
from src.ht_token import Token


# ---------------------------------------------------------------------------
# number_type
# ---------------------------------------------------------------------------
class TestNumberType:
    def test_cardinal_digit(self):
        assert number_type("5", set(), set()) == "cardinal"

    def test_cardinal_word(self):
        assert number_type("five", {"five"}, set()) == "cardinal"

    def test_ordinal_word(self):
        assert number_type("first", set(), {"first"}) == "ordinal"

    def test_ordinal_numeric(self):
        assert number_type("1st", set(), set()) == "ordinal"
        assert number_type("22nd", set(), set()) == "ordinal"
        assert number_type("3rd", set(), set()) == "ordinal"
        assert number_type("4th", set(), set()) == "ordinal"

    def test_unknown(self):
        assert number_type("abc", set(), set()) is None

    def test_empty(self):
        assert number_type("", set(), set()) is None
        assert number_type(None, set(), set()) is None

    def test_hyphenated_cardinal(self):
        assert number_type("twenty-one", {"twenty", "one"}, set()) == "cardinal"

    def test_hyphenated_ordinal(self):
        result = number_type("twenty-first", {"twenty"}, {"first"})
        assert result == "ordinal"

    def test_fraction(self):
        assert number_type("2/3", set(), set()) == "cardinal"


# ---------------------------------------------------------------------------
# is_possessive_or_s
# ---------------------------------------------------------------------------
class TestPossessive:
    def test_apostrophe_s(self):
        assert is_possessive_or_s("Ali's") is True
        assert is_possessive_or_s("student's") is True

    def test_s_apostrophe(self):
        assert is_possessive_or_s("students'") is True
        assert is_possessive_or_s("teachers'") is True

    def test_pronouns(self):
        for p in ['my', 'your', 'his', 'her', 'its', 'our', 'their']:
            assert is_possessive_or_s(p) is True

    def test_regular_word(self):
        assert is_possessive_or_s("hello") is False
        assert is_possessive_or_s("books") is False

    def test_empty(self):
        assert is_possessive_or_s("") is False
        assert is_possessive_or_s(None) is False


# ---------------------------------------------------------------------------
# possessive_before_index
# ---------------------------------------------------------------------------
class TestPossessiveBeforeIndex:
    def test_finds_pronoun(self):
        words = ["my", "red", "book"]
        assert possessive_before_index(words, 2) is True

    def test_finds_apostrophe_s(self):
        words = ["Ali", "'s", "book"]
        assert possessive_before_index(words, 2) is True

    def test_blocked_by_strong_punct(self):
        words = ["his", ".", "books"]
        assert possessive_before_index(words, 2) is False

    def test_no_possessive(self):
        words = ["the", "red", "book"]
        assert possessive_before_index(words, 2) is False

    def test_idx_zero(self):
        assert possessive_before_index(["my", "book"], 0) is False

    def test_with_tokens(self):
        tokens = [
            Token("her", "", "", index=0),
            Token("books", "", "", index=1),
        ]
        assert possessive_before_index(tokens, 1) is True

    def test_comma_does_not_block(self):
        words = ["his", ",", "books"]
        assert possessive_before_index(words, 2) is True


# ---------------------------------------------------------------------------
# is_np_boundary
# ---------------------------------------------------------------------------
class TestNPBoundary:
    def test_punctuation(self):
        for p in [".", "!", "?", ";", ":", ","]:
            assert is_np_boundary(p) is True

    def test_conjunction(self):
        for c in ["and", "but", "or", "nor", "yet", "so"]:
            assert is_np_boundary(c) is True

    def test_preposition(self):
        for p in ["in", "on", "at", "by", "with", "from"]:
            assert is_np_boundary(p) is True

    def test_verb(self):
        # فقط حس غالب (syns[0]) معیار است — نه any verb sense
        # 'believe' / 'happen' حس اول WordNet فعل است
        assert is_np_boundary("believe") is True
        assert is_np_boundary("happen") is True

    def test_noun_primary_not_boundary(self):
        # 'run' و 'book' حس غالب اسم‌اند → مرز NP نیستند
        # (قبلاً any(verb) آن‌ها را به اشتباه مرز می‌کرد)
        assert is_np_boundary("run") is False
        assert is_np_boundary("book") is False

    def test_regular_word(self):
        assert is_np_boundary("hello") is False

    def test_empty(self):
        assert is_np_boundary("") is False


# ---------------------------------------------------------------------------
# is_punctuation, is_and_word
# ---------------------------------------------------------------------------
class TestSimpleHelpers:
    def test_is_punctuation(self):
        assert is_punctuation(".") is True
        assert is_punctuation(",") is True
        assert is_punctuation("hello") is False

    def test_is_and_word(self):
        assert is_and_word("and") is True
        assert is_and_word("AND") is True
        assert is_and_word("or") is False


# ---------------------------------------------------------------------------
# syllable_count
# ---------------------------------------------------------------------------
class TestSyllableCount:
    def test_monosyllable(self):
        assert syllable_count("cat") == 1
        assert syllable_count("run") == 1

    def test_multisyllable(self):
        assert syllable_count("beautiful") >= 3
        assert syllable_count("happy") >= 2

    def test_unknown_word(self):
        assert syllable_count("xyzq") >= 1


# ---------------------------------------------------------------------------
# preprocess_text / tokenize_english
# ---------------------------------------------------------------------------
class TestPreprocessTokenize:
    def test_preprocess_separates_punct(self):
        result = preprocess_text("Hello,world!")
        assert "Hello" in result
        assert "," in result
        assert "world" in result

    def test_preprocess_possessive(self):
        result = preprocess_text("Ali's book")
        assert "Ali 's" in result

    def test_tokenize_basic(self):
        tokens = tokenize_english("Hello world")
        assert tokens == ["Hello", "world"]

    def test_tokenize_keeps_possessive(self):
        tokens = tokenize_english("Ali 's book")
        assert "Ali" in tokens
        assert "'s" in tokens

    def test_tokenize_punctuation(self):
        tokens = tokenize_english("Hello . world")
        assert "." in tokens
