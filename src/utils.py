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
# NLTK setup
# =============================================================================
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


# =============================================================================
# مدیریت فایل و مسیرها
# =============================================================================
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


# =============================================================================
# توابع کمکی پردازش متن
# =============================================================================
PUNCTUATION = {".", ",", "!", "?", ";", ":", "…", "—", "–",
               ")", "(", "[", "]", "{", "}", "«", "»"}

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
    poss = {'my', 'your', 'his', 'her', 'its', 'our', 'their',
            'mine', 'yours', 'hers', 'ours', 'theirs'}
    return w in poss

def is_np_boundary(token):
    if not token:
        return False
    t = str(token).lower()
    if t in {".", "!", "?", ";", ":", "—", ","}:
        return True
    if re.search(r'[.!?;:—]$', t):
        return True
    preps = {'in', 'on', 'at', 'by', 'with', 'from', 'to', 'for', 'about',
             'under', 'over', 'between', 'among', 'during', 'before',
             'after', 'since', 'until', 'into', 'onto'}
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
        # wordnet هنوز دانلود نشده — بدون crash فقط False
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


# ---------- cmudict با کش (برای سرعت) ----------
_CMU_CACHE = None

def _get_cmu():
    """برگرداندن dict سی‌ام‌یو؛ اگر دیتا نباشد dict خالی."""
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
    # fallback: شمارش خوشه‌های واکه
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

    # پشتیبانی از Context جدید و dict قدیمی
    if ctx is not None:
        vq = ctx.get('vague_quant_set') if hasattr(ctx, 'get') else None
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
    """جدا کردن علائم نگارشی به جز آپوستروف."""
    pattern = r"([A-Za-z0-9])([.,!?;:\(\)\[\]\{\}«»…—–])"
    text = re.sub(pattern, r"\1 \2", text)
    pattern = r"([.,!?;:\(\)\[\]\{\}«»…—–])([A-Za-z0-9])"
    text = re.sub(pattern, r"\1 \2", text)
    return text


# =============================================================================
# 🆕 توابع جدید برای Pipeline
# =============================================================================
def preprocess_text(text):
    """سه مرحلهٔ نرمال‌سازی متن قبل از توکن‌سازی."""
    text = separate_punct_except_apostrophe(text)
    text = re.sub(r'([.!?])([a-zA-Z])', r'\1 \2', text)
    text = re.sub(r"(\w)'s\b", r"\1 's", text)  # normalize possessives
    return text


def tokenize_english(text):
    """توکن‌سازی انگلیسی با حفظ 's و s' در انتها."""
    return re.findall(r"\w+(?:['’]s|s')|\S+", text)
