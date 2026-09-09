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

# =============================================================================
# تنظیمات اولیه NLTK
# =============================================================================
def setup_nltk():
    required_packages = ['punkt', 'wordnet', 'cmudict']
    missing_packages = []
    for package in required_packages:
        try:
            nltk.data.find(f'tokenizers/{package}' if package == 'punkt' else f'corpora/{package}')
        except LookupError:
            missing_packages.append(package)
    if missing_packages:
        logging.info(f"دانلود دیتاهای NLTK: {', '.join(missing_packages)}")
        for package in missing_packages:
            nltk.download(package, quiet=True)

# =============================================================================
# مدیریت فایل و مسیرها
# =============================================================================
def ensure_dir(path):
    if not os.path.exists(path):
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

# =============================================================================
# توابع کمکی پردازش متن (که قبلاً در processor.py بودند)
# =============================================================================
PUNCTUATION = {".", ",", "!", "?", ";", ":", "…", "—", "–", ")", "(", "[", "]", "{", "}", "«", "»"}

def is_punctuation(token):
    return token in PUNCTUATION

def is_and_word(word):
    return word.lower() == 'and'

def is_possessive_or_s(word):
    if not word:
        return False
    w = str(word).lower().strip()
    if w.endswith("'s") or w.endswith("s'"):
        return True
    poss = {'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs'}
    return w in poss

def is_np_boundary(token):
    if not token:
        return False
    t = str(token).lower()
    if t in {".", "!", "?", ";", ":", "—", ","}:
        return True
    if re.search(r'[.!?;:—]$', t):
        return True
    preps = {'in', 'on', 'at', 'by', 'with', 'from', 'to', 'for', 'about', 'under', 'over',
             'between', 'among', 'during', 'before', 'after', 'since', 'until', 'into', 'onto'}
    if t in preps:
        return True
    if t in {'and', 'but', 'or', 'nor', 'yet', 'so'}:
        return True
    if t in {")", "]", "}", '"', "'"}:
        return True
    syns = wn.synsets(t)
    if syns and syns[0].pos() == 'v':
        return True
    return False

def is_cardinal_word(word, cardinal_numbers):
    w = word.lower()
    return w.isdigit() or w in cardinal_numbers

def is_ordinal_word(word, ordinal_numbers):
    w = word.lower()
    return (w in ordinal_numbers or re.match(r'^\d+(st|nd|rd|th)$', w) or w in ['st', 'nd', 'rd', 'th'])

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
    if ('/' in lowered or any(kw in lowered for kw in ['half', 'third', 'quarter', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'hundredth', 'thousandth'])):
        return 'cardinal'
    return None

def syllable_count(word):
    from nltk.corpus import cmudict
    _cmu = cmudict.dict()
    w = word.lower()
    w_clean = re.sub(r"[^\w'-]", '', w)
    try:
        pron = _cmu[w_clean][0]
        return sum(1 for p in pron if re.search(r'\d', p))
    except:
        return max(1, len(re.findall(r'[aeiouy]+', w_clean, re.I)))

def is_uncountable_noun(word, ctx=None):
    if ctx is None:
        ctx = {}
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
    if ctx.get('vague_quant_set') and w in ctx['vague_quant_set']:
        return True
    syns = wn.synsets(w, pos='n')
    if not syns:
        return False
    for syn in syns:
        definition = syn.definition().lower()
        if any(phrase in definition for phrase in ['amount of', 'quantity of', 'mass of', 'substance', 'uncountable', 'mass noun']):
            return True
        for hyper_path in syn.hypernym_paths():
            for hyper in hyper_path:
                hyper_name = hyper.name()
                if 'substance.n.01' in hyper_name or 'abstraction.n.06' in hyper_name:
                    return True
    if wn.synsets(w + 's', pos='n') == [] and syns:
        return True
    return False
