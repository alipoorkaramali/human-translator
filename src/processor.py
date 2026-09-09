# =============================================================================
# processor.py - پردازشگر اصلی
# =============================================================================

import pandas as pd
import nltk
import re
from nltk.corpus import wordnet as wn
from nltk.corpus import cmudict

# استفاده از import مطلق به جای نسبی
from src.utils import (
    is_possessive_or_s, is_np_boundary, number_type, syllable_count,
    is_uncountable_noun, is_and_word, is_punctuation, separate_punct_except_apostrophe
)
from src.rules import apply_all_rules

nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('cmudict', quiet=True)

_cmu = cmudict.dict()

def load_phrases_from_excel(excel_file='Book1.xlsx'):
    try:
        df = pd.read_excel(excel_file, engine='openpyxl')
        article_set     = set(df['article'].dropna().astype(str).str.strip().str.lower()) if 'article' in df.columns else set()
        demotrative_set = set(df['demotrative'].dropna().astype(str).str.strip().str.lower()) if 'demotrative' in df.columns else set()
        simple_set      = set(df['simple'].dropna().astype(str).str.strip().str.lower()) if 'simple' in df.columns else set()
        compound_set    = set(df['compound'].dropna().astype(str).str.strip().str.lower()) if 'compound' in df.columns else set()
        cardinal_set    = set(df['cardinal'].dropna().astype(str).str.strip().str.lower()) if 'cardinal' in df.columns else set()
        ordinal_set     = set(df['ordinal'].dropna().astype(str).str.strip().str.lower()) if 'ordinal' in df.columns else set()
        intensifier_set = set(df['adverbs of intensifiers'].dropna().astype(str).str.strip().str.lower()) if 'adverbs of intensifiers' in df.columns else set()
        vague_quant_set = set(df['vague_quantifiers'].dropna().astype(str).str.strip().str.lower()) if 'vague_quantifiers' in df.columns else set()
        phrases_set = article_set | demotrative_set | simple_set | compound_set
        return (phrases_set, cardinal_set, ordinal_set, article_set,
                demotrative_set, simple_set, compound_set, intensifier_set, vague_quant_set)
    except Exception as e:
        print("خطا در بارگذاری اکسل:", e)
        return set(), set(), set(), set(), set(), set(), set(), set(), set()

def normalize_possessives(text):
    return re.sub(r"(\w)'s\b", r"\1 's", text)

def merge_fractions(tokens, i):
    if i >= len(tokens):
        return None, i, False
    t = tokens[i]
    if re.match(r'^\d+/\d+$', t):
        return t, i+1, True
    if '-' in t or '‐' in t or '–' in t or '—' in t:
        clean_t = t.replace('‐', '-').replace('–', '-').replace('—', '-')
        parts = clean_t.split('-')
        last = parts[-1].lower()
        ordinal_endings = {'half','third','thirds','quarter','quarters','fourth','fourths',
                          'fifth','fifths','sixth','seventh','eighth','ninth','tenth',
                          'eleventh','twelfth','hundredth','hundredths','thousandth','thousandths',
                          'millionth','billionth'}
        if any(last.rstrip('s').endswith(end) for end in ['th','rd','nd','st','half','quarter','third','fourth']):
            if last not in {'ray','level','shaped','term','commerce','known'}:
                return t, i+1, True
    if re.match(r'^\d+[-‐–—]\d+/\d+$', t.replace(' ', '')):
        return t, i+1, True
    if i+1 < len(tokens) and tokens[i].isdigit() and re.match(r'^\d+/\d+$', tokens[i+1]):
        return tokens[i] + "-" + tokens[i+1], i+2, True
    if i+1 < len(tokens):
        w1, w2 = tokens[i].lower(), tokens[i+1].lower()
        cardinals = {'one','two','three','four','five','six','seven','eight','nine','ten',
                     'eleven','twelve','thirteen','fourteen','fifteen','sixteen',
                     'seventeen','eighteen','nineteen','twenty','thirty','forty','fifty',
                     'sixty','seventy','eighty','ninety','hundred'}
        fractions = {'half','halves','third','thirds','quarter','quarters','fourth','fourths',
                     'fifth','fifths','sixth','seventh','eighth','ninth','tenth'}
        if w1 in cardinals and w2 in fractions:
            return tokens[i] + " " + tokens[i+1], i+2, True
    if i+3 < len(tokens) and tokens[i+1].lower() == 'and':
        if tokens[i+2].lower() in ['a','an','one','two','three','four','five','six','seven','eight','nine']:
            if i+3 < len(tokens) and tokens[i+3].lower().rstrip('s') in {'half','third','quarter','fourth'}:
                return " ".join(tokens[i:i+4]), i+4, True
    cardinals2 = {'one','two','three','four','five','six','seven','eight','nine','ten',
                  'eleven','twelve','thirteen','fourteen','fifteen','sixteen',
                  'seventeen','eighteen','nineteen','twenty','thirty','forty','fifty',
                  'sixty','seventy','eighty','ninety','hundred'}
    if i+4 < len(tokens) and tokens[i+1].lower() == 'and' and tokens[i+2].lower() in cardinals2 and \
       tokens[i+4].lower().rstrip('s') in fractions:
        return " ".join(tokens[i:i+5]), i+5, True
    return None, i, False

# بقیه توابع postprocess (apply_law_sh_fixed, apply_law_z_fixed, apply_the_ordinal_rule,
# _final_fix_quantifier_after_noun, apply_wordnet_and_final_rules, postprocess)
# را دقیقاً به همان شکلی که قبلاً بودید می‌گذاریم، اما با import مطلق از src.utils

# ... (بقیه توابع را از نسخه قبلی کپی کنید)
# فقط مطمئن شوید که توابع کمکی را از src.utils import می‌کنید.

def process_text(text, excel_file='Book1.xlsx', output_file='data/output/output.xlsx'):
    (phrases_set, cardinal_numbers, ordinal_numbers, article_set,
     demotrative_set, simple_set, compound_set, intensifier_set, vague_quant_set) = load_phrases_from_excel(excel_file)

    text = separate_punct_except_apostrophe(text)
    text = re.sub(r'([.!?])([a-zA-Z])', r'\1 \2', text)
    text = normalize_possessives(text)
    tokens = re.findall(r"\w+(?:['’]s|s')|\S+", text)

    out_words, out_labels, out_numtype = [], [], []
    i = 0

    while i < len(tokens):
        w = tokens[i]
        wl = w.lower()
        nt = number_type(w, cardinal_numbers, ordinal_numbers)

        merged, new_i, is_fraction = merge_fractions(tokens, i)
        if is_fraction:
            out_words.append(merged)
            out_labels.append('m1')
            last_part = merged.strip().split()[-1].lower()
            last_clean = re.sub(r'[.,]', '', last_part)
            if (last_clean in ordinal_numbers or re.match(r'^\d+(st|nd|rd|th)$', last_clean) or
                last_clean.endswith(('st', 'nd', 'rd', 'th'))):
                frac_type = 'ordinal'
            else:
                frac_type = 'cardinal'
            out_numtype.append(frac_type)
            i = new_i
            continue

        # ... (بقیه کدهای حلقه while را دقیقاً مثل قبل)
        # اما مطمئن شوید که توابع کمکی مانند is_np_boundary, is_possessive_or_s
        # از src.utils import شده‌اند.

    ctx = {
        'phrases_set': phrases_set, 'cardinal_numbers': cardinal_numbers,
        'ordinal_numbers': ordinal_numbers, 'article_set': article_set,
        'demotrative_set': demotrative_set, 'simple_set': simple_set,
        'compound_set': compound_set, 'intensifier_set': intensifier_set,
        'vague_quant_set': vague_quant_set
    }

    out_words, out_labels, out_numtype, dict_roles = postprocess(out_words, out_labels, out_numtype, ctx)
    out_words, out_labels, out_numtype = apply_all_rules(out_words, out_labels, out_numtype, ctx)

    df_out = pd.DataFrame({
        'کلمه': out_words,
        'برچسب': out_labels,
        'نوع_عدد': out_numtype,
        'نقش_از_دیکشنری': dict_roles
    })
    df_out.to_excel(output_file, index=False, engine='openpyxl')
    return df_out
