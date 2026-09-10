# tests/test_core/test_token.py
import pytest
from src.token import Token


class TestTokenDefaults:
    def test_word_only(self):
        t = Token(word='hello')
        assert t.word == 'hello'
        assert t.label == ''
        assert t.numtype == ''
        assert t.role == 'unknown'
        assert t.locked is False

    def test_original_autofilled(self):
        t = Token(word='hello')
        assert t.original == 'hello'

    def test_original_explicit(self):
        t = Token(word='hello', original='Hello!')
        assert t.original == 'Hello!'


class TestTokenToDict:
    def test_keys(self):
        t = Token(word='hello', label='N')
        d = t.to_dict()
        assert set(d.keys()) == {'کلمه', 'برچسب', 'نوع_عدد', 'نقش_از_دیکشنری'}

    def test_values(self):
        t = Token(word='books', label='N', numtype='', role='noun')
        d = t.to_dict()
        assert d['کلمه'] == 'books'
        assert d['برچسب'] == 'N'
        assert d['نقش_از_دیکشنری'] == 'noun'


class TestTokenMethods:
    def test_copy(self):
        t1 = Token('hello', label='N')
        t2 = t1.copy(label='m1')
        assert t1.label == 'N'
        assert t2.label == 'm1'
        assert t1 is not t2

    def test_is_empty(self):
        assert Token('').is_empty() is True
        assert Token('   ').is_empty() is True
        assert Token('hello').is_empty() is False

    def test_reset_label(self):
        t = Token('hello', label='m1', numtype='cardinal', role='quant')
        t.reset_label()
        assert t.label == ''
        assert t.numtype == ''
        assert t.role == 'unknown'

    def test_repr_short(self):
        t = Token('hello', label='N', index=3)
        r = repr(t)
        assert 'hello' in r
        assert 'N' in r
        assert '3' in r

    def test_repr_locked(self):
        t = Token('hello', label='N', locked=True)
        assert '🔒' in repr(t)
