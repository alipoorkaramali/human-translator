import pytest
from src.ht_token import Token


def test_token_creation():
    t = Token('hello')
    assert t.word == 'hello'
    assert t.label == ''
    assert t.original == 'hello'


def test_token_to_dict():
    t = Token('five', 'm1', 'cardinal', role='number')
    d = t.to_dict()
    assert d['کلمه'] == 'five'
    assert d['برچسب'] == 'm1'
    assert d['نوع_عدد'] == 'cardinal'
    assert d['نقش_از_دیکشنری'] == 'number'


def test_token_copy():
    t = Token('test', 'm1')
    t2 = t.copy(label='m2', locked=True)
    assert t2.label == 'm2'
    assert t2.locked is True
    assert t.label == 'm1'  # original unchanged


def test_token_is_empty():
    assert Token('').is_empty()
    assert Token('  ').is_empty()
    assert not Token('a').is_empty()


def test_token_reset_label():
    t = Token('x', 'm1', 'cardinal', role='num')
    t.reset_label()
    assert t.label == ''
    assert t.numtype == ''
    assert t.role == 'unknown'
