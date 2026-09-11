# tests/test_core/test_pipeline.py
import os
import pytest

# اگر Pipeline آماده نیست، تست skip شود
Pipeline = pytest.importorskip("src.core.pipeline").Pipeline


BOOK = os.path.join(os.path.dirname(__file__), '..', '..', 'Book1.xlsx')
skip_no_book = pytest.mark.skipif(
    not os.path.exists(BOOK),
    reason="Book1.xlsx موجود نیست"
)


@skip_no_book
class TestPipeline:
    def test_construct(self):
        pipe = Pipeline(excel_file=BOOK)
        assert pipe.ctx is not None
        assert pipe.registry is not None

    def test_run_simple(self):
        pipe = Pipeline(excel_file=BOOK)
        df = pipe.run("some books are here")
        assert len(df) > 0
        assert set(df.columns) >= {'کلمه', 'برچسب', 'نوع_عدد', 'نقش_از_دیکشنری'}

    def test_run_with_number(self):
        pipe = Pipeline(excel_file=BOOK)
        df = pipe.run("five books")
        # 'five' باید cardinal باشد
        five_row = df[df['کلمه'].str.lower() == 'five']
        assert len(five_row) == 1
        assert five_row.iloc[0]['نوع_عدد'] == 'cardinal'
