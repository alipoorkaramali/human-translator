import pytest
from src.ht_token import Token


@pytest.fixture
def make_token():
    def _make(word, label='', numtype='', role='unknown', locked=False, index=-1):
        return Token(word=word, label=label, numtype=numtype, role=role,
                     locked=locked, index=index)
    return _make


@pytest.fixture
def sample_tokens():
    from src.ht_token import Token
    return [
        Token('The', 'm1', '', index=0),
        Token('first', 'm1', 'ordinal', index=1),
        Token('book', '', '', index=2),
    ]
