"""واردکنندهٔ ۱: Book1.xlsx + NLTK (WordNet + cmudict)"""
import os
import pandas as pd
import nltk
from nltk.corpus import wordnet as wn
from nltk.corpus import cmudict

from ..context import Context
from src.utils import DEFAULT_PREPOSITIONS


def load_nltk_data(nltk_data_path: str = None):
    if nltk_data_path is None:
        nltk_data_path = os.environ.get(
            'NLTK_DATA', os.path.join(os.getcwd(), 'nltk_data'))
    if os.path.exists(nltk_data_path) and nltk_data_path not in nltk.data.path:
        nltk.data.path.insert(0, nltk_data_path)
    for pkg, sub in [('punkt', 'tokenizers'),
                     ('wordnet', 'corpora'),
                     ('cmudict', 'corpora')]:
        try:
            nltk.data.find(f'{sub}/{pkg}')
        except LookupError:
            nltk.download(pkg, quiet=True)


def load_excel(excel_file: str = 'Book1.xlsx') -> dict:
    df = pd.read_excel(excel_file, engine='openpyxl')

    def col(name):
        if name in df.columns:
            return set(df[name].dropna().astype(str).str.strip().str.lower())
        return set()

    article_set     = col('article')
    demotrative_set = col('demotrative')
    simple_set      = col('simple')
    compound_set    = col('compound')
    cardinal_set    = col('cardinal')
    ordinal_set     = col('ordinal')
    intensifier_set = col('adverbs of intensifiers')
    vague_quant_set = col('vague_quantifiers')

    # ستون اختیاری preposition / prepositions در Excel
    excel_preps = col('preposition') | col('prepositions')
    preposition_set = set(DEFAULT_PREPOSITIONS) | excel_preps

    return {
        'phrases_set':      article_set | demotrative_set | simple_set | compound_set,
        'cardinal_numbers': cardinal_set,
        'ordinal_numbers':  ordinal_set,
        'article_set':      article_set,
        'demotrative_set':  demotrative_set,
        'simple_set':       simple_set,
        'compound_set':     compound_set,
        'intensifier_set':  intensifier_set,
        'vague_quant_set':  vague_quant_set,
        'preposition_set':  preposition_set,
    }


def build_context(excel_file: str = 'Book1.xlsx',
                  nltk_data_path: str = None) -> Context:
    load_nltk_data(nltk_data_path)
    ctx = Context()
    for k, v in load_excel(excel_file).items():
        setattr(ctx, k, v)
    if not getattr(ctx, 'preposition_set', None):
        ctx.preposition_set = set(DEFAULT_PREPOSITIONS)
    ctx.cmu = cmudict.dict()
    ctx.wn  = wn
    return ctx
