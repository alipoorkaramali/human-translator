# =============================================================================
# utils.py - توابع کمکی و عمومی
# =============================================================================

import os
import sys
import re
import logging
import nltk
from nltk.corpus import wordnet as wn
from nltk.corpus import cmudict
from pathlib import Path


def setup_nltk():
    """بررسی و آماده‌سازی دیتاهای NLTK."""
    nltk_path = os.environ.get('NLTK_DATA', '/usr/share/nltk_data')
    if os.path.exists(nltk_path) and nltk_path not in nltk.data.path:
        nltk.data.path.insert(0, nltk_path)
        logging.info(f"مسیر NLTK_DATA اضافه شد: {nltk_path}")

    required_packages = ['punkt', 'wordnet', 'cmudict']
    missing_packages = []

    for package in required_packages:
        try:
            nltk.data.find(f'tokenizers/{package}' if package == 'punkt'
                           else f'corpora/{package}')
            logging.info(f"✅ {package} موجود است.")
        except LookupError:
            missing_packages.append(package)

    if missing_packages:
        logging.warning(f"⚠️ دیتاهای زیر پیدا نشدند: {', '.join(missing_packages)}")
        for package in missing_packages:
            try:
                nltk.download(package, quiet=True)
            except Exception as e:
                logging.error(f"دانلود {package} ناموفق بود: {e}")
    else:
        logging.info("✅ همه‌ی دیتاهای NLTK موجود هستند.")


def ensure_dir(path):
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        logging.info(f"پوشه ساخته شد: {path}")
    return path

def get_project_root():
    return Path(__file__).resolve().parent.parent

def read_text_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"خطا در خواندن فایل {file_path}: {e}")
        sys.exit(1)

def save_text_file(file_path, content):
    ensure_dir(os.path.dirname(file_path))
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logging.info(f"فایل ذخیره شد: {file_path}")

def setup_logging(level=logging.INFO, log_file=None):
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        ensure_dir(os.path.dirname(log_file))
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    logging.basicConfig(level=level, format=log_format, handlers=handlers)


PUNCTUATION = {".", ",", "!", "?", ";", ":", "…", "—", "–",
               ")", "(", "[", "]", "{", "}", "«", "»"}

_STRONG_STOP = {".", "!", "?", ";", ":", "—"}

_PRONOUN_POSSESSIVES = {
    'my', 'your', 'his', 'her', 'its', 'our', 'their',
    'mine', 'yours', 'hers', 'ours', 'theirs',
}

# ---------------------------------------------------------------------------
# حروف اضافه — منبع پیش‌فرض مرز NP (قابل گسترش از Excel: preposition)
# of و as عمداً مرز NP نیستند (قانون ض / of-quantifier).
# ---------------------------------------------------------------------------
DEFAULT_PREPOSITIONS = {
    'in', 'on', 'at', 'by', 'with', 'from', 'to', 'for', 'about',
    'under', 'over', 'between', 'among', 'amongst', 'during', 'before',
    'after', 'since', 'until', 'till', 'into', 'onto', 'upon',
    'across', 'through', 'along', 'around', 'round', 'near', 'beside',
    'besides', 'behind', 'beyond', 'inside', 'outside', 'above', 'below',
    'beneath', 'within', 'without', 'against', 'toward', 'towards',
    'via', 'per', 'plus', 'minus', 'unlike', 'like', 'except', 'despite',
    'throughout', 'underneath', 'amid', 'amidst', 'atop',
    'up', 'down', 'off', 'out', 'past', 'next',
}

def is_punctuation(token):
    return token in PUNCTUATION

def is_and_word(word):
    return word.lower() == 'and'

def is_possessive_pronoun(word):
    """فقط ضمیر ملکی (my/his/…) — نه students'."""
    if not word:
        return False
    return str(word).lower().strip() in _PRONOUN_POSSESSIVES

def is_possessive_or_s(word):
    if not word:
        return False
    w = str(word).lower().strip()
    if w.endswith("'s") or w.endswith("s'"):
        return True
    return w in _PRONOUN_POSSESSIVES


def _token_text(item) -> str:
    if item is None:
        return ""
    if hasattr(item, "word"):
        return str(item.word)
    return str(item)


def possessive_before_index(sequence, idx, max_lookback=15) -> bool:
    if not sequence or idx is None or idx <= 0:
        return False

    j = idx - 1
    limit = max(0, idx - max_lookback)

    while j >= limit:
        text = _token_text(sequence[j]).strip()
        if not text:
            j -= 1
            continue

        if text in _STRONG_STOP or text[-1:] in _STRONG_STOP:
            return False

        if is_possessive_or_s(text):
            return True

        j -= 1

    return False


def is_np_boundary(token, preposition_set=None):
    """
    مرز گروه اسمی (NP boundary).

    موارد مرز:
      - علائم نگارشی قوی
      - حروف اضافه (DEFAULT_PREPOSITIONS یا preposition_set از Context/Excel)
      - ربط‌دهنده‌ها (and/but/or/…)
      - فعل فقط اگر حس غالب WordNet (syns[0]) فعل باشد

    of و as عمداً در DEFAULT نیستند تا قانون ض و of-quantifier نشکنند.
    """
    if not token:
        return False
    t = str(token).lower()
    if hasattr(token, "word"):
        t = str(token.word).lower()

    if " " in t:
        return False

    if t in {".", "!", "?", ";", ":", "—", ","}:
        return True
    if re.search(r'[.!?;:—]$', t):
        return True

    preps = preposition_set if preposition_set is not None else DEFAULT_PREPOSITIONS
    if t in preps:
        return True

    if t in {'and', 'but', 'or', 'nor', 'yet', 'so'}:
        return True
    if t in {")", "]", "}", '"', "'"}:
        return True
    try:
        syns = wn.synsets(t)
        if syns and syns[0].pos() == 'v':
            return True
    except LookupError:
        pass
    return False

def is_cardinal_word(word, cardinal_numbers):
    w = word.lower()
    return w.isdigit() or w in cardinal_numbers

def is_ordinal_word(word, ordinal_numbers):
    w = word.lower()
    return (w in ordinal_numbers or
            re.match(r'^\d+(st|nd|rd|th)$', w) or
            w in ['st', 'nd', 'rd', 'th'])

def number_type(word, cardinal_numbers, ordinal_numbers):
    if not word:
        return None
    w_clean = re.sub(r'[.,]', '', word.lower())
    if w_clean.isdigit() or w_clean in cardinal_numbers:
        return 'cardinal'
    if re.match(r'^\d+(st|nd|rd|th)$', w_clean) or w_clean in ordinal_numbers:
        return 'ordinal'
    if '-' in word:
        parts = word.lower().split('-')
        clean_parts = [p for p in parts if not is_and_word(p)]
        if len(clean_parts) >= 2 and is_ordinal_word(clean_parts[-1], ordinal_numbers):
            if all(is_cardinal_word(p, cardinal_numbers) for p in clean_parts[:-1]):
                return 'ordinal'
        if all(is_cardinal_word(p, cardinal_numbers) or is_and_word(p) for p in parts):
            return 'cardinal'
    lowered = word.lower()
    if ('/' in lowered or any(kw in lowered for kw in
            ['half', 'third', 'quarter', 'fourth', 'fifth', 'sixth',
             'seventh', 'eighth', 'ninth', 'tenth', 'hundredth', 'thousandth'])):
        return 'cardinal'
    return None


_CMU_CACHE = None

def _get_cmu():
    global _CMU_CACHE
    if _CMU_CACHE is None:
        try:
            _CMU_CACHE = cmudict.dict()
        except LookupError:
            _CMU_CACHE = {}
    return _CMU_CACHE

def syllable_count(word):
    w = word.lower()
    w_clean = re.sub(r"[^\w'-]", '', w)
    try:
        cmu = _get_cmu()
        if w_clean in cmu:
            pron = cmu[w_clean][0]
            return sum(1 for p in pron if re.search(r'\d', p))
    except (KeyError, IndexError, TypeError):
        pass
    return max(1, len(re.findall(r'[aeiouy]+', w_clean, re.I)))


def is_uncountable_noun(word, ctx=None):
    w = word.lower().strip()
    common_uncountables = {
        'water', 'time', 'money', 'information', 'news', 'furniture', 'advice',
        'knowledge', 'equipment', 'luggage', 'music', 'art', 'love', 'happiness',
        'rice', 'bread', 'milk', 'coffee', 'tea', 'wine', 'beer', 'food', 'sugar',
        'research', 'evidence', 'progress', 'work', 'homework', 'traffic', 'weather',
        'damage', 'permission', 'travel', 'fun', 'luck', 'health', 'education',
        'violence', 'pollution', 'air', 'electricity', 'light', 'heat', 'space'
    }
    if w in common_uncountables:
        return True

    if ctx is not None:
        vq = None
        if hasattr(ctx, 'get'):
            vq = ctx.get('vague_quant_set')
        elif hasattr(ctx, 'vague_quant_set'):
            vq = getattr(ctx, 'vague_quant_set', None)
        if vq and w in vq:
            return True

    try:
        syns = wn.synsets(w, pos='n')
    except LookupError:
        return False
    if not syns:
        return False
    for syn in syns:
        definition = syn.definition().lower()
        if any(phrase in definition for phrase in
               ['amount of', 'quantity of', 'mass of', 'substance',
                'uncountable', 'mass noun']):
            return True
        for hyper_path in syn.hypernym_paths():
            for hyper in hyper_path:
                name = hyper.name()
                if 'substance.n.01' in name or 'abstraction.n.06' in name:
                    return True
    try:
        if wn.synsets(w + 's', pos='n') == [] and syns:
            return True
    except LookupError:
        pass
    return False


def separate_punct_except_apostrophe(text):
    pattern = r"([A-Za-z0-9])([.,!?;:\(\)\[\]\{\}«»…—–])"
    text = re.sub(pattern, r"\1 \2", text)
    pattern = r"([.,!?;:\(\)\[\]\{\}«»…—–])([A-Za-z0-9])"
    text = re.sub(pattern, r"\1 \2", text)
    return text


def preprocess_text(text):
    text = separate_punct_except_apostrophe(text)
    text = re.sub(r'([.!?])([a-zA-Z])', r'\1 \2', text)
    text = re.sub(r"(\w)'s\b", r"\1 's", text)
    return text


def tokenize_english(text):
    return re.findall(r"\w+(?:['’]s|s')|\S+", text)
