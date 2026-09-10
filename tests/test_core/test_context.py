# tests/test_core/test_context.py
import pytest
from src.core.context import Context


class TestContextDefaults:
    def test_empty(self):
        ctx = Context()
        assert ctx.article_set == set()
        assert ctx.cardinal_numbers == set()
        assert ctx.wn is None
        assert ctx.cmu == {}


class TestContextDictLike:
    def test_getitem(self):
        ctx = Context()
        ctx.article_set = {'a', 'the'}
        assert ctx['article_set'] == {'a', 'the'}

    def test_setitem(self):
        ctx = Context()
        ctx['article_set'] = {'a'}
        assert ctx.article_set == {'a'}

    def test_get_with_default(self):
        ctx = Context()
        assert ctx.get('missing', default=set()) == set()

    def test_get_existing(self):
        ctx = Context()
        ctx.simple_set = {'many'}
        assert ctx.get('simple_set') == {'many'}

    def test_keys(self):
        ctx = Context()
        keys = ctx.keys()
        assert 'article_set' in keys
        assert 'cardinal_numbers' in keys


class TestContextUpdate:
    def test_update_from_tuple(self):
        ctx = Context()
        tup = (
            {'phrases'},      # phrases_set
            {'one'},          # cardinal
            {'first'},        # ordinal
            {'a', 'the'},     # article
            {'this'},         # demonstrative
            {'many'},         # simple
            {'a lot of'},     # compound
            {'very'},         # intensifier
            {'plenty'},       # vague_quant
        )
        ctx.update_from_tuple(tup)
        assert ctx.phrases_set == {'phrases'}
        assert ctx.article_set == {'a', 'the'}
        assert ctx.cardinal_numbers == {'one'}
