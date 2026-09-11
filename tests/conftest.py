import os
from pathlib import Path

import pytest

from src.ht_token import Token


@pytest.fixture(scope="session", autouse=True)
def _ensure_nltk_path():
    """مسیر دیتای NLTK را برای تست‌ها تنظیم می‌کند."""
    try:
        import nltk
    except ImportError:
        return

    root = Path(__file__).resolve().parent.parent
    candidates = [
        os.environ.get("NLTK_DATA"),
        str(root / "nltk_data"),
        "/usr/share/nltk_data",
        str(Path.home() / "nltk_data"),
    ]
    for p in candidates:
        if p and Path(p).exists() and p not in nltk.data.path:
            nltk.data.path.insert(0, p)


@pytest.fixture
def make_token():
    def _make(word, label='', numtype='', role='unknown', locked=False, index=-1):
        return Token(word=word, label=label, numtype=numtype, role=role,
                     locked=locked, index=index)
    return _make


@pytest.fixture
def sample_tokens():
    return [
        Token('The', 'm1', '', index=0),
        Token('first', 'm1', 'ordinal', index=1),
        Token('book', '', '', index=2),
    ]
