# =============================================================================
# processor.py
# تمام توابع پردازش متن (برچسب‌زنی کمیت‌نماها، اعداد، صفات، قیود و ...)
# شامل قوانین اختصاصی m1 تا m5 (با استفاده از rules.py)
# =============================================================================

import pandas as pd
import nltk
import re
from nltk.corpus import wordnet as wn
from nltk.corpus import cmudict

# وارد کردن قوانین اختصاصی
from .rules import apply_all_rules

# =============================================================================
# ۰. بارگذاری اولیه NLTK (در صورت نیاز، فقط یکبار انجام میشه)
# =============================================================================
nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('cmudict', quiet=True)

_cmu = cmudict.dict()   # برای شمارش سیلاب‌های more/most


# =============================================================================
# ۱. بارگذاری مجموعه‌های کلمات از فایل اکسل (Book1.xlsx)
# =============================================================================
def load_phrases_from_excel(excel_file='Book1.xlsx'):
    """
    بارگذاری مجموعه‌های کلمات از فایل اکسل.
    ستون‌های مورد انتظار:
    article, demotrative, simple, compound, cardinal, ordinal,
    adverbs of intensifiers, vague_quantifiers
    """
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


# =============================================================================
# ۲. توابع کمکی (پردازش اولیه)
# =============================================================================
def normalize_possessives(text):
    """جدا کردن 's و s' از کلمه‌ی قبل"""
    text = re.sub(r"(\w)'s\b", r"\1 's", text)
    return text


PUNCTUATION = {".", ",", "!", "?", ";", ":", "…", "—", "–", ")", "(", "[", "]", "{", "}", "«", "»"}

def is_punctuation(token):
    return token in PUNCTUATION


def is_cardinal_word(word, cardinal_numbers):
    w = word.lower()
    return w.isdigit() or w in cardinal_numbers


def is_ordinal_word(word, ordinal_numbers):
    w = word.lower()
    return (w in ordinal_numbers or 
            re.match(r'^\d+(st|nd|rd|th)$', w) or 
            w in ['st', 'nd', 'rd', 'th'])


def is_and_word(word):
    return word.lower() == 'and'


def number_type(word, cardinal_numbers, ordinal_numbers):
    """تشخیص نوع عدد: cardinal, ordinal یا None"""
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

    # تشخیص کسر به عنوان cardinal
    lowered = word.lower()
    if ('/' in lowered or 
        any(kw in lowered for kw in ['half', 'third', 'quarter', 'fourth', 'fifth', 'sixth', 
                                    'seventh', 'eighth', 'ninth', 'tenth', 'hundredth', 'thousandth'])):
        return 'cardinal'

    return None


def is_possessive_or_s(word):
    """تشخیص همه حالت‌های ملکی: 's و s'"""
    if not word:
        return False
    w = str(word).lower().strip()
    if w.endswith("'s") or w.endswith("s'"):
        return True
    poss = {'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs'}
    return w in poss


def is_np_boundary(token):
    """تشخیص مرز گروه اسمی (NP)"""
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


def possessive_before_index(out_words, idx, max_lookback=15):
    """بررسی وجود ضمیر ملکی قبل از idx (بدون مداخله‌ی punctuation)"""
    j = idx - 1
    limit = max(0, idx - max_lookback)
    while j >= limit:
        token = out_words[j]
        if token in {".", "!", "?", ";", ":"}:
            return False
        if is_possessive_or_s(token):
            return True
        j -= 1
    return False


def syllable_count(word):
    """شمارش سیلاب‌ها برای قانون more/most"""
    w = word.lower()
    w_clean = re.sub(r"[^\w'-]", '', w)
    try:
        pron = _cmu[w_clean][0]
        return sum(1 for p in pron if re.search(r'\d', p))
    except:
        return max(1, len(re.findall(r'[aeiouy]+', w_clean, re.I)))


def separate_punct_except_apostrophe(text):
    """جدا کردن علائم نگارشی به جز آپوستروف"""
    pattern = r"([A-Za-z0-9])([.,!?;:\(\)\[\]\{\}«»…—–])"
    text = re.sub(pattern, r"\1 \2", text)
    pattern = r"([.,!?;:\(\)\[\]\{\}«»…—–])([A-Za-z0-9])"
    text = re.sub(pattern, r"\1 \2", text)
    return text


def is_uncountable_noun(word, ctx=None):
    """تشخیص اسم غیرقابل شمارش (uncountable)"""
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
        if any(phrase in definition for phrase in [
            'amount of', 'quantity of', 'mass of', 'substance', 'uncountable', 'mass noun'
        ]):
            return True
        for hyper_path in syn.hypernym_paths():
            for hyper in hyper_path:
                hyper_name = hyper.name()
                if 'substance.n.01' in hyper_name or 'abstraction.n.06' in hyper_name:
                    return True

    if wn.synsets(w + 's', pos='n') == [] and syns:
        return True

    return False


# =============================================================================
# ۳. قوانین ترکیب کسرها
# =============================================================================
def merge_fractions(tokens, i):
    """تشخیص و ادغام کسرها (مانند one-half, 2/3, three quarters و ...)"""
    if i >= len(tokens):
        return None, i, False

    t = tokens[i]

    # 1. اسلشی ساده
    if re.match(r'^\d+/\d+$', t):
        return t, i+1, True

    # 2. هیفن‌دار با ordinal ending
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

    # 3. 2-1/2 style
    if re.match(r'^\d+[-‐–—]\d+/\d+$', t.replace(' ', '')):
        return t, i+1, True

    # 4. 2 1/2 style
    if i+1 < len(tokens) and tokens[i].isdigit() and re.match(r'^\d+/\d+$', tokens[i+1]):
        return tokens[i] + "-" + tokens[i+1], i+2, True

    # 5. one half, three quarters, ...
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

    # 6. one and a half / two and three quarters
    if i+3 < len(tokens) and tokens[i+1].lower() == 'and':
        if tokens[i+2].lower() in ['a','an','one','two','three','four','five','six','seven','eight','nine']:
            if i+3 < len(tokens) and tokens[i+3].lower().rstrip('s') in {'half','third','quarter','fourth'}:
                return " ".join(tokens[i:i+4]), i+4, True
    
    # 7. one and one third / two and seven eighths
    cardinals2 = {'one','two','three','four','five','six','seven','eight','nine','ten',
                  'eleven','twelve','thirteen','fourteen','fifteen','sixteen',
                  'seventeen','eighteen','nineteen','twenty','thirty','forty','fifty',
                  'sixty','seventy','eighty','ninety','hundred'}
    if i+4 < len(tokens) and tokens[i+1].lower() == 'and' and tokens[i+2].lower() in cardinals2 and \
       tokens[i+4].lower().rstrip('s') in fractions:
        return " ".join(tokens[i:i+5]), i+5, True

    return None, i, False


# =============================================================================
# ۴. قوانین پس‌پردازش اصلی (postprocess)
# =============================================================================
def apply_law_sh_fixed(out_words, out_labels, out_numtype, ctx):
    """قانون ش (a/an + صفت + سرگروه جمع)"""
    singular_heads = {
        "number", "amount", "kind", "type", "sort", "deal", "pile", "bunch", "bit",
        "set", "group", "variety", "lot", "sum", "many", "quantity"
    }

    i = 0
    while i < len(out_words) - 2:
        if possessive_before_index(out_words, i, max_lookback=15):
            i += 1
            continue

        if out_words[i].lower() not in {"a", "an"}:
            i += 1
            continue

        start = i
        k = i + 1

        while k < len(out_words):
            word = out_words[k].lower()
            label = out_labels[k]

            if label in ['m2', 'adv']:
                k += 1
                continue
            if label == '' and wn.synsets(word) and wn.synsets(word)[0].pos() in 'as':
                k += 1
                continue
            if word in ctx.get('vague_quant_set', set()):
                k += 1
                continue
            break

        if (k < len(out_words) and 
            out_words[k].lower() in singular_heads and 
            k+1 < len(out_words) and 
            out_words[k+1].lower() == 'of'):

            combined = " ".join(out_words[start:k+2])
            out_words[start:k+2] = [combined]
            out_labels[start:k+2] = ['m1']
            out_numtype[start:k+2] = ['']

            i = start + 1
        else:
            i += 1


def apply_law_z_fixed(out_words, out_labels, out_numtype, ctx):
    """قانون ض (کمیت‌نما + سرگروه جمع + of)"""
    plural_heads = {
        "numbers", "amounts", "kinds", "types", "sorts", "groups", "varieties",
        "bunches", "piles", "bits", "sets", "lots", "ranges", "series", "volumes",
        "heaps", "loads", "tons", "dozens", "scores", "myriads", "multitudes"
    }
    vague_quant_set = ctx.get('vague_quant_set', set())

    i = 0
    while i < len(out_words) - 1:
        start = i

        # تعیین محدوده‌ی NP جاری
        np_boundary = i
        while np_boundary < len(out_words):
            if is_np_boundary(out_words[np_boundary]):
                np_boundary += 1
                break
            np_boundary += 1

        # بررسی وجود ضمیر ملکی در کل NP
        possessive_exists_in_np = False
        for j in range(i, np_boundary):
            if is_possessive_or_s(out_words[j]):
                possessive_exists_in_np = True
                break

        if possessive_exists_in_np:
            i = np_boundary
            continue

        modifier_end = i
        has_real_m1 = False

        while modifier_end < len(out_words) - 1 and modifier_end < np_boundary:
            word = out_words[modifier_end]
            label = out_labels[modifier_end]
            word_low = word.lower() if isinstance(word, str) else str(word).lower()

            if label == 'm1':
                phrase = word if ' ' in word else word_low
                if phrase not in vague_quant_set:
                    has_real_m1 = True

            if label in ['m2', 'adv']:
                modifier_end += 1
                continue
            if label == '' and wn.synsets(word_low) and wn.synsets(word_low)[0].pos() in 'as':
                modifier_end += 1
                continue
            if word_low in vague_quant_set:
                modifier_end += 1
                continue
            if label == 'm1':
                modifier_end += 1
                continue
            break

        head_idx = modifier_end
        of_idx = modifier_end + 1

        if (head_idx >= len(out_words) or 
            out_words[head_idx].lower() not in plural_heads or
            of_idx >= len(out_words) or 
            out_words[of_idx].lower() != 'of'):
            i = start + 1
            continue

        if of_idx + 1 < len(out_words):
            next_w = out_words[of_idx + 1].lower()
            if wn.synsets(next_w) and wn.synsets(next_w)[0].pos() == 'v':
                i = start + 1
                continue

        if modifier_end == start:
            i = start + 1
            continue

        if has_real_m1:
            i = of_idx + 1
            continue

        combined = " ".join(out_words[start:of_idx + 1])
        out_words[start:of_idx + 1] = [combined]
        out_labels[start:of_idx + 1] = ['m1']
        out_numtype[start:of_idx + 1] = ['']

        i = start + 1


def apply_the_ordinal_rule(out_words, out_labels, out_numtype):
    """قانون the + ordinal → m1 | ordinal بدون the → adv"""
    i = 0
    while i < len(out_words) - 1:
        if len(out_numtype) <= i + 1 or out_numtype[i + 1] != 'ordinal':
            i += 1
            continue
        if out_labels[i + 1] in ['m4', 'adv']:
            i += 1
            continue
        if out_words[i].lower() == 'the' and out_labels[i] in ['', 'm1']:
            combined = f"the {out_words[i + 1]}"
            out_words[i]   = combined
            out_labels[i]  = 'm1'
            out_numtype[i] = 'ordinal'
            del out_words[i + 1]
            del out_labels[i + 1]
            del out_numtype[i + 1]
        else:
            out_labels[i + 1] = 'adv'
            i += 1


def _final_fix_quantifier_after_noun(out_words, out_labels, out_numtype):
    """آخرین قانون اصلاح‌کننده: m1 بعد از اسم → m4 (عدد) یا adv (غیرعدد)"""
    for i in range(1, len(out_words)):
        if out_labels[i] != 'm1':
            continue

        current_word = out_words[i]
        current_lower = current_word.lower()

        if current_lower in {'a', 'an', 'the', 'this', 'that', 'these', 'those'}:
            continue

        is_number = (out_numtype[i] in ['cardinal', 'ordinal']) or \
                    number_type(current_word, set(), set()) is not None

        has_noun_without_of = False
        for j in range(i-1, -1, -1):
            if is_np_boundary(out_words[j]):
                break
            if out_words[j].lower() == 'of':
                break
            if out_labels[j] == 'N':
                has_noun_without_of = True
                break

        if has_noun_without_of:
            if is_number:
                out_labels[i] = 'm4'
            else:
                out_labels[i] = 'adv'


def apply_wordnet_and_final_rules(out_words, out_labels, out_numtype, ctx):
    """قوانین نهایی WordNet و نقش‌های دیکشنری"""
    dict_roles = ['unknown'] * len(out_words)

    for i, w in enumerate(out_words):
        label = out_labels[i]
        is_multi = ' ' in w

        if is_multi and label == 'm1':
            dict_roles[i] = 'quantifier_phrase (multi-word)'
            continue

        if label == 'm1':
            dict_roles[i] = 'determiner/quantifier'

        syns = wn.synsets(w.lower())
        if syns:
            if out_numtype[i] == 'ordinal':
                the_before = (i > 0 and out_words[i-1].lower() == 'the')
                noun_after = (i+1 < len(out_labels) and out_labels[i+1] == 'N')
                if not (the_before or noun_after):
                    out_labels[i] = 'adv'
                    dict_roles[i] = 'adverb'
                    continue

            pos = syns[0].pos()
            role_map = {'n': 'noun', 'v': 'verb', 'a': 'adjective',
                        's': 'adjective (satellite)', 'r': 'adverb'}
            dict_roles[i] = role_map.get(pos, 'unknown')
            mapping = {'a': 'm2', 's': 'm2', 'r': 'adv', 'n': 'N', 'v': 'V'}
            if out_labels[i] in ['', 'm2', 'N', 'V']:
                if pos in mapping:
                    out_labels[i] = mapping[pos]
        else:
            dict_roles[i] = 'unknown'

    # intensifierها
    for i, w in enumerate(out_words):
        if w.lower() in ctx.get('intensifier_set', set()):
            out_labels[i] = 'adv'
            dict_roles[i] = 'adverb (intensifier)'

    # more/most بعد از m1 → m2
    for i in range(1, len(out_words)):
        if out_words[i].lower() in ['more', 'most']:
            has_m1_before = False
            j = i - 1
            while j >= 0:
                if is_np_boundary(out_words[j]):
                    break
                if out_labels[j] in ['m2', 'adv'] or out_words[j].lower() in {',', 'and', 'but', 'or'}:
                    break
                if out_labels[j] == 'm1':
                    has_m1_before = True
                    break
                j -= 1
            if has_m1_before:
                out_labels[i] = 'm2'
                dict_roles[i] = 'adjective (comparative)'

    # more/most + صفت چندسیلابی → adv
    for i in range(len(out_words)-1):
        if out_words[i].lower() in ['more', 'most']:
            if out_labels[i+1] == 'm2' and syllable_count(out_words[i+1]) > 1:
                out_labels[i] = 'adv'
                dict_roles[i] = 'adverb (comparative/superlative)'

    # کلمات خاص
    for i, w in enumerate(out_words):
        lw = w.lower()
        if lw == 'of':
            out_labels[i] = ''
            dict_roles[i] = 'preposition'
        elif re.match(r'^[^\w\s]$', w):
            dict_roles[i] = 'punctuation'
        elif lw in {'a', 'an', 'the'}:
            dict_roles[i] = 'determiner/article'

        if dict_roles[i] == 'unknown':
            role_map = {'m1': 'determiner/quantifier', 'm2': 'adjective',
                        'adv': 'adverb', 'N': 'noun', 'V': 'verb', '': 'function word'}
            dict_roles[i] = role_map.get(out_labels[i], 'unknown')

    # قانون little / a little
    for i in range(len(out_words)):
        current_word = out_words[i].lower()
        if 'little' in current_word:
            if i + 1 < len(out_words) and out_labels[i + 1] == 'N':
                next_noun = out_words[i + 1]
                if current_word == 'a little':
                    out_labels[i] = 'm1'
                    dict_roles[i] = 'determiner/quantifier'
                elif current_word == 'little':
                    if is_uncountable_noun(next_noun, ctx):
                        out_labels[i] = 'm1'
                        dict_roles[i] = 'determiner/quantifier'
                    else:
                        out_labels[i] = 'm2'
                        dict_roles[i] = 'adjective'

    # enough بعد از صفت → adv
    for i in range(len(out_words)):
        if out_words[i].lower() == 'enough':
            if i > 0 and out_labels[i - 1] == 'm2':
                out_labels[i] = 'adv'
                dict_roles[i] = 'adverb'

    return out_words, out_labels, out_numtype, dict_roles


def postprocess(out_words, out_labels, out_numtype, ctx):
    """قلب پس‌پردازش – اجرای تمام قوانین به ترتیب"""
    max_iterations = 8
    for iteration in range(max_iterations):
        changed = False

        # قانون some + عدد → adv (با استثناهای compound)
        for i in range(len(out_words) - 1):
            if out_words[i].lower() == 'some' and out_labels[i] != 'adv':
                next_word = out_words[i + 1]
                if number_type(next_word, ctx['cardinal_numbers'], ctx['ordinal_numbers']):
                    lookahead = ' '.join(out_words[i:i+6]).lower()
                    if (lookahead.startswith('some hundred') or
                        lookahead.startswith('some thousand') or
                        lookahead.startswith('some dozen') or
                        lookahead.startswith('some score') or
                        'some hundreds' in lookahead or
                        'some thousands' in lookahead or
                        'some dozens' in lookahead):
                        continue
                    if any(comp in lookahead for comp in ctx['compound_set'] if comp.startswith('some ')):
                        continue
                    out_labels[i] = 'adv'
                    changed = True

        # تفکیک مجدد compoundهایی که قبلاً m1 بودند
        i = 0
        while i < len(out_words):
            if ' ' in out_words[i] and out_labels[i] in ['', 'adv']:
                parts = out_words[i].split()
                sub_labels = []
                for j, p in enumerate(parts):
                    pl = p.lower()
                    if pl in ctx['phrases_set'] or ' '.join(parts[max(0,j-1):j+1]).lower() in ctx['compound_set']:
                        sub_labels.append('m1')
                    else:
                        sub_labels.append('')
                sub_num = [number_type(p, ctx['cardinal_numbers'], ctx['ordinal_numbers']) or '' for p in parts]
                out_words[i:i+1] = parts
                out_labels[i:i+1] = sub_labels
                out_numtype[i:i+1] = sub_num
                changed = True
            i += 1

        # N of → N
        for i in range(len(out_words)-1):
            if out_labels[i] == 'm1' and out_words[i+1].lower() == 'of':
                out_labels[i] = 'N'
                changed = True

        # بعد از of → کلمات بعدی اسم (N)
        for i in range(len(out_words)):
            if out_words[i].lower() == 'of':
                k = i + 1
                while k < len(out_words) and out_words[k].lower() != 'of':
                    w = out_words[k].lower()
                    if out_labels[k] == '':
                        if w in ctx['phrases_set']:
                            out_labels[k] = 'm1'
                            changed = True
                        else:
                            syns = wn.synsets(w)
                            if syns and syns[0].pos() == 'n':
                                out_labels[k] = 'N'
                                changed = True
                    k += 1

        # more/most بعد از det/poss → adv
        for i in range(1, len(out_words)):
            if out_words[i].lower() in ['more', 'most'] and out_labels[i] in ['m1', 'm2']:
                prev = out_words[i-1].lower()
                if prev in ctx['article_set'] | ctx['demotrative_set'] or is_possessive_or_s(prev):
                    out_labels[i] = 'adv'
                    changed = True

        # دو quantifier پشت سر هم (به جز some)
        for i in range(1, len(out_words)):
            prev = out_words[i-1].lower()
            cur  = out_words[i].lower()
            prev_q = (prev in ctx['simple_set'] | ctx['compound_set'] or 
                     out_numtype[i-1] in ['cardinal', 'ordinal'])
            cur_q  = (cur in ctx['simple_set'] | ctx['compound_set'] or 
                     out_numtype[i] in ['cardinal', 'ordinal'])
            if prev_q and cur_q and prev != 'some':
                out_labels[i] = '' if cur in ctx['compound_set'] else 'adv'
                changed = True

        # much قبل از صفت یا قید → adv
        for i in range(len(out_words)-1):
            if out_words[i].lower() == 'much':
                next_label = out_labels[i+1] if i+1 < len(out_labels) else ''
                if next_label in ['m2', 'adv']:
                    out_labels[i] = 'adv'
                    changed = True
                elif out_labels[i] in ['m1', ''] and next_label == '':
                    next_word = out_words[i+1].lower()
                    syns = wn.synsets(next_word)
                    if syns and syns[0].pos() in ['a', 's', 'r']:
                        out_labels[i] = 'adv'
                        changed = True

        # much به تنهایی → adv
        for i in range(len(out_words)):
            if out_words[i].lower() == 'much' and out_labels[i] in ['', None]:
                out_labels[i] = 'adv'
                changed = True

        # اعتبارسنجی m1های اشتباه (بعد از اسم)
        for i in range(1, len(out_words)):
            if out_labels[i] != 'm1':
                continue
            current_word = out_words[i]
            current_lower = current_word.lower()
            if current_lower in {'a', 'an', 'the', 'this', 'that', 'these', 'those'}:
                continue
            is_number = (out_numtype[i] in ['cardinal', 'ordinal']) or \
                        number_type(current_word, set(), set()) is not None
            has_noun_without_of = False
            for j in range(i-1, -1, -1):
                if is_np_boundary(out_words[j]):
                    break
                if out_words[j].lower() == 'of':
                    break
                if out_labels[j] == 'N':
                    has_noun_without_of = True
                    break
            if has_noun_without_of:
                if is_number:
                    out_labels[i] = 'm4'
                else:
                    out_labels[i] = 'adv'
                changed = True

        if not changed and iteration >= 3:
            break

    # اجرای قوانین خاص (ش و ض)
    apply_law_sh_fixed(out_words, out_labels, out_numtype, ctx)
    apply_law_z_fixed(out_words, out_labels, out_numtype, ctx)
    apply_the_ordinal_rule(out_words, out_labels, out_numtype)

    # قوانین نهایی WordNet
    out_words, out_labels, out_numtype, dict_roles = apply_wordnet_and_final_rules(
        out_words, out_labels, out_numtype, ctx
    )

    # آخرین اصلاح: عدد/quantifier بعد از اسم
    _final_fix_quantifier_after_noun(out_words, out_labels, out_numtype)

    # قانون نهایی more بعد از m1 → m2 (دوباره برای اطمینان)
    for i in range(1, len(out_words)):
        if out_words[i].lower() == 'more':
            has_m1_before = False
            j = i - 1
            while j >= 0:
                if is_np_boundary(out_words[j]):
                    break
                if out_labels[j] in ['m2', 'adv'] or out_words[j].lower() in {',', 'and', 'but', 'or'}:
                    break
                if out_labels[j] == 'm1':
                    has_m1_before = True
                    break
                j -= 1
            if has_m1_before:
                out_labels[i] = 'm2'
                dict_roles[i] = 'adjective (comparative)'

    return out_words, out_labels, out_numtype, dict_roles


# =============================================================================
# ۵. تابع اصلی پردازش (process_text)
# =============================================================================
def process_text(text, excel_file='Book1.xlsx', output_file='data/output/output.xlsx'):
    """
    تابع اصلی پردازش متن.
    ورودی: متن (string)
    خروجی: دیتافریم پانداز و ذخیره‌سازی در فایل اکسل
    """
    (phrases_set, cardinal_numbers, ordinal_numbers, article_set,
     demotrative_set, simple_set, compound_set, intensifier_set, vague_quant_set) = load_phrases_from_excel(excel_file)

    # جدا کردن علائم
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

        # ۱. قانون کسر
        merged, new_i, is_fraction = merge_fractions(tokens, i)
        if is_fraction:
            out_words.append(merged)
            out_labels.append('m1')
            last_part = merged.strip().split()[-1].lower()
            last_clean = re.sub(r'[.,]', '', last_part)
            if (last_clean in ordinal_numbers or 
                re.match(r'^\d+(st|nd|rd|th)$', last_clean) or
                last_clean.endswith(('st', 'nd', 'rd', 'th'))):
                frac_type = 'ordinal'
            else:
                frac_type = 'cardinal'
            out_numtype.append(frac_type)
            i = new_i
            continue

        # ۲. tens of, hundreds of, ...
        unit_bases = {
            'ten', 'tens', 'hundred', 'hundreds', 'thousand', 'thousands',
            'million', 'millions', 'billion', 'billions', 'trillion', 'trillions'
        }
        if wl in unit_bases and i+1 < len(tokens) and tokens[i+1].lower() == 'of':
            current_phrase = f"{w} of"
            out_words.append(current_phrase)
            out_labels.append('m1')
            out_numtype.append('')
            i += 2
            while i < len(tokens) - 1:
                next_w = tokens[i].lower()
                if next_w in unit_bases and tokens[i+1].lower() == 'of':
                    current_phrase += f" {tokens[i]} of"
                    out_words[-1] = current_phrase
                    i += 2
                else:
                    break
            continue

        # ۳. simple + of (با جلوگیری از تکرار کمیت‌نما)
        if (wl in simple_set or (nt and nt == 'cardinal')) and i+1 < len(tokens) and tokens[i+1].lower() == 'of':
            has_previous_quantifier = False
            for j in range(i-1, max(i-12, 0), -1):
                prev = tokens[j].lower()
                if is_np_boundary(tokens[j]) or prev in {",", "and", "but", "or"}:
                    break
                if (prev in simple_set or 
                    prev in {'all','some','no','any','every','each','more','most','less','few','several','much','little','enough'} or
                    number_type(tokens[j], cardinal_numbers, ordinal_numbers)):
                    has_previous_quantifier = True
                    break
            if has_previous_quantifier:
                out_words.append(w)
                out_labels.append('')
                out_numtype.append(nt or '')
            else:
                combined = f"{w} of"
                out_words.append(combined)
                out_labels.append('m1')
                out_numtype.append(nt or '')
            i += 2
            continue

        # ۴. عبارات چندکلمه‌ای (تا ۵ کلمه)
        found = False
        for length in range(min(6, len(tokens)-i), 1, -1):
            phrase_tokens = tokens[i:i+length]
            phrase = ' '.join(phrase_tokens).lower()

            blocked_by_possessive = False
            blocked_by_modifier  = False
            for j in range(i-1, -1, -1):
                if j >= len(tokens):
                    continue
                if is_np_boundary(tokens[j]):
                    break
                if is_possessive_or_s(tokens[j]):
                    blocked_by_possessive = True
                if j < len(out_labels) and out_labels[j] in {'m2', 'adv'}:
                    blocked_by_modifier = True

            if blocked_by_possessive or blocked_by_modifier:
                continue
            if any(is_possessive_or_s(tok) for tok in phrase_tokens):
                continue

            has_previous_quantifier = False
            for j in range(i-1, max(i-12, 0), -1):
                if j >= len(tokens):
                    continue
                prev = tokens[j].lower()
                if is_np_boundary(tokens[j]) or prev in {",", "and", "but", "or"}:
                    break
                if (prev in simple_set or 
                    prev in {'all','some','no','any','every','each','more','most','less','few','several','much','little','enough'} or
                    number_type(tokens[j], cardinal_numbers, ordinal_numbers)):
                    has_previous_quantifier = True
                    break

            if has_previous_quantifier:
                continue

            if phrase in phrases_set:
                out_words.append(' '.join(phrase_tokens))
                out_labels.append('m1')
                out_numtype.append('')
                i += length
                found = True
                break

        if found:
            continue

        # ۵. اعداد مرکب معمولی
        if nt:
            seq = [w]
            j = i + 1
            while j < len(tokens):
                next_token = tokens[j]
                next_type = number_type(next_token, cardinal_numbers, ordinal_numbers)
                if next_type:
                    seq.append(next_token)
                    j += 1
                    continue
                if is_and_word(next_token) and j + 1 < len(tokens):
                    next_next_type = number_type(tokens[j + 1], cardinal_numbers, ordinal_numbers)
                    if next_next_type:
                        seq.append(next_token)
                        j += 1
                        continue
                break

            combined_number = ' '.join(seq)
            out_words.append(combined_number)
            last_word = seq[-1].lower()
            last_clean = re.sub(r'[.,]', '', last_word)
            if (last_clean in ordinal_numbers or 
                re.match(r'^\d+(st|nd|rd|th)$', last_clean) or
                last_clean.endswith(('st', 'nd', 'rd', 'th', 'first', 'second', 'third', 'fourth', 'fifth',
                                    'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth'))):
                final_type = 'ordinal'
            else:
                final_type = 'cardinal'
            out_labels.append('m1' if final_type == 'cardinal' else '')
            out_numtype.append(final_type)
            i = j
            continue

        # ۶. پیش‌فرض
        out_words.append(w)
        out_labels.append('m1' if wl in phrases_set else '')
        out_numtype.append('')

        # قانون ویژه: اسم جمع + 's یا s' → N
        if re.search(r"['’]s$|s'$", w, re.I):
            base = re.sub(r"['’]s$|s'$", "", w.lower())
            syns = wn.synsets(base)
            if syns and syns[0].pos() == 'n':
                out_labels[-1] = 'N'
            elif out_labels[-1] != 'm1':
                out_labels[-1] = 'N'

        i += 1

    # --------------------------------------------------------------
    # پس‌پردازش نهایی
    # --------------------------------------------------------------
    ctx = {
        'phrases_set': phrases_set, 'cardinal_numbers': cardinal_numbers, 'ordinal_numbers': ordinal_numbers,
        'article_set': article_set, 'demotrative_set': demotrative_set,
        'simple_set': simple_set, 'compound_set': compound_set,
        'intensifier_set': intensifier_set, 'vague_quant_set': vague_quant_set
    }

    # ۱. اجرای پس‌پردازش اصلی (postprocess)
    out_words, out_labels, out_numtype, dict_roles = postprocess(
        out_words, out_labels, out_numtype, ctx
    )

    # ۲. اجرای قوانین اختصاصی m1 تا m5 (قوانین جدید از rules.py)
    out_words, out_labels, out_numtype = apply_all_rules(
        out_words, out_labels, out_numtype, ctx
    )

    # --------------------------------------------------------------
    # ذخیره خروجی
    # --------------------------------------------------------------
    df_out = pd.DataFrame({
        'کلمه': out_words,
        'برچسب': out_labels,
        'نوع_عدد': out_numtype,
        'نقش_از_دیکشنری': dict_roles
    })

    df_out.to_excel(output_file, index=False, engine='openpyxl')
    return df_out
