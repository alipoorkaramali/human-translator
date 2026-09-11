# tests/test_importers/test_data_importer.py
import os
import pytest

data_importer = pytest.importorskip("src.core.importers.data_importer")

BOOK = os.path.join(os.path.dirname(__file__), '..', '..', 'Book1.xlsx')
skip_no_book = pytest.mark.skipif(
    not os.path.exists(BOOK),
    reason="Book1.xlsx موجود نیست"
)


@skip_no_book
class TestLoadExcel:
    def test_returns_dict(self):
        data = data_importer.load_excel(BOOK)
        assert isinstance(data, dict)

    def test_expected_keys(self):
        data = data_importer.load_excel(BOOK)
        for key in ['phrases_set', 'cardinal_numbers', 'ordinal_numbers',
                    'article_set', 'demotrative_set', 'simple_set',
                    'compound_set', 'intensifier_set', 'vague_quant_set']:
            assert key in data
            assert isinstance(data[key], set)

    def test_phrases_set_is_union(self):
        data = data_importer.load_excel(BOOK)
        expected = (data['article_set'] | data['demotrative_set'] |
                    data['simple_set'] | data['compound_set'])
        assert data['phrases_set'] == expected


@skip_no_book
class TestBuildContext:
    def test_context_has_sets(self):
        ctx = data_importer.build_context(BOOK)
        assert ctx.article_set is not None
        assert ctx.cardinal_numbers is not None

    def test_context_has_wn_and_cmu(self):
        ctx = data_importer.build_context(BOOK)
        assert ctx.wn is not None
        assert isinstance(ctx.cmu, dict)
        assert len(ctx.cmu) > 0
