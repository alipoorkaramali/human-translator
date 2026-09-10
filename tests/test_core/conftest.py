# tests/conftest.py
# fixtureها و تنظیمات مشترک pytest
import os
import sys
import pytest

# اطمینان از دسترسی به src
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


# ---------------------------------------------------------------------------
# Context fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def empty_context():
    """Context کاملاً خالی."""
    from src.core.context import Context
    return Context()


@pytest.fixture
def basic_context():
    """Context با مجموعه‌های کوچک برای تست Ruleها."""
    from src.core.context import Context
    ctx = Context()
    ctx.article_set = {'a', 'an', 'the'}
    ctx.demotrative_set = {'this', 'that', 'these', 'those'}
    ctx.simple_set = {'many', 'few', 'several', 'some'}
    ctx.compound_set = {'a lot of', 'a few', 'a great many'}
    ctx.cardinal_numbers = {'one', 'two', 'three', 'four', 'five', 'hundred'}
    ctx.ordinal_numbers = {'first', 'second', 'third'}
    ctx.intensifier_set = {'very', 'quite', 'rather'}
    ctx.vague_quant_set = {'plenty', 'lots', 'tons'}
    ctx.phrases_set = (
        ctx.article_set | ctx.demotrative_set |
        ctx.simple_set | ctx.compound_set
    )
    return ctx


# ---------------------------------------------------------------------------
# Token fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def simple_tokens():
    """لیست توکن ساده: some books are"""
    from src.token import Token
    return [
        Token('some', 'm1', index=0),
        Token('books', 'N', index=1),
        Token('are', 'V', index=2),
    ]


@pytest.fixture
def number_tokens():
    """توکن‌های عددی: some + five"""
    from src.token import Token
    return [
        Token('some', 'm1', index=0),
        Token('five', 'm1', numtype='cardinal', index=1),
    ]
