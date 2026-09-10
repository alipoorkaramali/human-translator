# =============================================================================
# processor.py - wrapper سازگار با کد قدیمی
#
# این فایل دیگر منطق پردازش ندارد.
# فقط process_text را برای backward compatibility حفظ می‌کند
# و در پشت صحنه از src.core.pipeline.Pipeline استفاده می‌کند.
# =============================================================================

from src.core.pipeline import Pipeline


def process_text(text,
                 excel_file: str = 'Book1.xlsx',
                 output_file: str = 'data/output/output.xlsx'):
    """
    Backward-compatible wrapper.

    مثال:
        from src.processor import process_text
        df = process_text(open('input.txt').read())
    """
    pipe = Pipeline(excel_file=excel_file)
    return pipe.run(text, output_file=output_file)


# =============================================================================
# Re-export برای کد قدیمی که این توابع را از processor import می‌کرد
# =============================================================================
from src.utils import (
    is_possessive_or_s, is_np_boundary, number_type, syllable_count,
    is_uncountable_noun, is_and_word, is_punctuation,
    separate_punct_except_apostrophe, preprocess_text, tokenize_english,
)

__all__ = [
    'process_text',
    'is_possessive_or_s', 'is_np_boundary', 'number_type',
    'syllable_count', 'is_uncountable_noun', 'is_and_word',
    'is_punctuation', 'separate_punct_except_apostrophe',
    'preprocess_text', 'tokenize_english',
]
