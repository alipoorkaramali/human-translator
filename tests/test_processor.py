import pytest
from src.utils import number_type, is_possessive_or_s, is_np_boundary

def test_number_type():
    assert number_type("5", set(), set()) == "cardinal"
    assert number_type("first", set(), {"first"}) == "ordinal"
    assert number_type("abc", set(), set()) is None

def test_is_possessive_or_s():
    assert is_possessive_or_s("Ali's") == True
    assert is_possessive_or_s("students'") == True
    assert is_possessive_or_s("hello") == False

def test_is_np_boundary():
    assert is_np_boundary(".") == True
    assert is_np_boundary("and") == True
    assert is_np_boundary("hello") == False
