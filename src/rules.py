# =============================================================================
# rules.py
# قوانین اختصاصی برای هر برچسب (m1 تا m5)
# هر قانون به صورت یک تابع مجزا نوشته شده است تا به راحتی قابل تغییر باشد.
# =============================================================================

import re
from nltk.corpus import wordnet as wn
from .utils import is_possessive_or_s, is_np_boundary, number_type, syllable_count


# =============================================================================
# ۱. قوانین مربوط به m1 (Determiner / Quantifier)
# =============================================================================
def apply_m1_rules(out_words, out_labels, out_numtype, ctx):
    """
    قوانین اختصاصی برای برچسب m1 (determiner/quantifier):
    - حذف m1 از کلماتی که بعد از اسم می‌آیند (به جز موارد خاص)
    - تشخیص ترکیب‌های خاص مانند "a lot of", "a number of"
    - تشخیص "some" + عدد به عنوان adv (به جز در ترکیبات خاص)
    - جلوگیری از重叠 m1 (دو m1 پشت سر هم)
    """
    changed = False
    phrases_set = ctx.get('phrases_set', set())
    simple_set = ctx.get('simple_set', set())
    compound_set = ctx.get('compound_set', set())
    cardinal_numbers = ctx.get('cardinal_numbers', set())
    ordinal_numbers = ctx.get('ordinal_numbers', set())
    vague_quant_set = ctx.get('vague_quant_set', set())

    # قانون ۱: some + عدد → adv (به جز در ترکیبات خاص مانند "some hundreds")
    for i in range(len(out_words) - 1):
        if out_words[i].lower() == 'some' and out_labels[i] == 'm1':
            next_word = out_words[i + 1]
            if number_type(next_word, cardinal_numbers, ordinal_numbers):
                lookahead = ' '.join(out_words[i:i+6]).lower()
                # استثناهای ترکیبات some hundred/thousand/dozen
                if (lookahead.startswith('some hundred') or
                    lookahead.startswith('some thousand') or
                    lookahead.startswith('some dozen') or
                    lookahead.startswith('some score') or
                    'some hundreds' in lookahead or
                    'some thousands' in lookahead or
                    'some dozens' in lookahead):
                    continue
                if any(comp in lookahead for comp in compound_set if comp.startswith('some ')):
                    continue
                out_labels[i] = 'adv'
                changed = True

    # قانون ۲: دو m1 پشت سر هم → دومی را adv یا خالی کن (به جز موارد خاص)
    for i in range(1, len(out_words)):
        if out_labels[i - 1] == 'm1' and out_labels[i] == 'm1':
            prev = out_words[i - 1].lower()
            cur = out_words[i].lower()
            # اگر دومی در compound_set باشد یا قبلاً ترکیب شده باشد، دست نزن
            if cur in compound_set or ' ' in out_words[i]:
                continue
            # اگر اولی "a" یا "an" باشد و دومی "lot" یا "few" باشد، ترکیب کن
            if prev in {'a', 'an'} and cur in {'lot', 'few', 'number', 'great many'}:
                continue
            # در غیر این صورت، دومی را adv کن
            out_labels[i] = 'adv'
            changed = True

    # قانون ۳: m1 بعد از اسم (بدون "of" بین) → adv یا m4
    for i in range(1, len(out_words)):
        if out_labels[i] != 'm1':
            continue
        current_word = out_words[i]
        current_lower = current_word.lower()
        # مقاله‌ها و demonstrativeها استثنا هستند
        if current_lower in {'a', 'an', 'the', 'this', 'that', 'these', 'those'}:
            continue

        is_number = (out_numtype[i] in ['cardinal', 'ordinal']) or \
                    number_type(current_word, cardinal_numbers, ordinal_numbers) is not None

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
                out_labels[i] = 'm4'   # عدد بعد از اسم → m4
            else:
                out_labels[i] = 'adv'  # quantifier بعد از اسم → adv
            changed = True

    return out_words, out_labels, out_numtype, changed


# =============================================================================
# ۲. قوانین مربوط به m2 (Adjective)
# =============================================================================
def apply_m2_rules(out_words, out_labels, out_numtype, ctx):
    """
    قوانین اختصاصی برای برچسب m2 (adjective):
    - تشخیص صفت‌های مرکب (hyphenated adjectives)
    - more/most + صفت چندسیلابی → m2 (صفت مقایسه‌ای/عالی)
    - little + اسم countable → m2 (به معنی کوچک)
    """
    changed = False

    # قانون ۱: more/most + صفت چندسیلابی → m2
    for i in range(len(out_words) - 1):
        if out_words[i].lower() in ['more', 'most'] and out_labels[i] in ['m1', 'adv']:
            next_word = out_words[i + 1]
            if out_labels[i + 1] == 'm2' and syllable_count(next_word) > 1:
                out_labels[i] = 'm2'   # more/most تبدیل به صفت مقایسه‌ای می‌شوند
                changed = True

    # قانون ۲: little + اسم countable → m2 (صفت به معنی کوچک)
    for i in range(len(out_words) - 1):
        if out_words[i].lower() == 'little' and out_labels[i] == 'm1':
            next_word = out_words[i + 1]
            if out_labels[i + 1] == 'N':
                if not is_uncountable_noun(next_word, ctx):
                    out_labels[i] = 'm2'   # little book → صفت کوچک
                    changed = True

    # قانون ۳: صفت‌های مرکب با خط تیره (hyphenated)
    for i in range(len(out_words)):
        if '-' in out_words[i] and out_labels[i] == '':
            parts = out_words[i].split('-')
            if len(parts) >= 2:
                # اگر تمام اجزا adjective یا noun باشند → m2
                all_adj = True
                for part in parts:
                    syns = wn.synsets(part.lower())
                    if syns and syns[0].pos() not in ['a', 's']:
                        all_adj = False
                        break
                if all_adj:
                    out_labels[i] = 'm2'
                    changed = True

    return out_words, out_labels, out_numtype, changed


# =============================================================================
# ۳. قوانین مربوط به m3 (تخصیص داده نشده – می‌توانید customize کنید)
# =============================================================================
def apply_m3_rules(out_words, out_labels, out_numtype, ctx):
    """
    قوانین اختصاصی برای برچسب m3:
    (فعلاً خالی است – می‌توانید قوانین خود را اینجا اضافه کنید)
    مثال: possessive pronouns, reflexive pronouns, etc.
    """
    changed = False

    # مثال: تشخیص ضمایر ملکی (my, your, his, her, its, our, their) به عنوان m3
    possessive_pronouns = {'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs'}
    for i in range(len(out_words)):
        if out_words[i].lower() in possessive_pronouns and out_labels[i] in ['', 'm1']:
            out_labels[i] = 'm3'
            changed = True

    return out_words, out_labels, out_numtype, changed


# =============================================================================
# ۴. قوانین مربوط به m4 (Number after noun)
# =============================================================================
def apply_m4_rules(out_words, out_labels, out_numtype, ctx):
    """
    قوانین اختصاصی برای برچسب m4 (عدد بعد از اسم):
    - اعداد بعد از اسم (مثل chapter 5, page twenty)
    - اعداد ترتیبی بعد از اسم (مثل World War II)
    - اعداد با پسوندهای خاص (st, nd, rd, th)
    """
    changed = False
    ordinal_numbers = ctx.get('ordinal_numbers', set())

    for i in range(len(out_words)):
        if out_labels[i] != 'm4':
            continue

        # اگر عدد قبلش اسم باشد و بعدش هیچ‌چیز نباشد → m4
        if i > 0 and out_labels[i - 1] == 'N':
            # بررسی اینکه آیا عدد واقعاً یک عدد است
            if out_numtype[i] in ['cardinal', 'ordinal']:
                # m4 بماند
                continue
            else:
                # اگر عدد نبود، adv کن
                out_labels[i] = 'adv'
                changed = True

        # اگر عدد ترتیبی تنها آمده باشد (بدون "the") → m5
        if out_numtype[i] == 'ordinal':
            the_before = (i > 0 and out_words[i-1].lower() == 'the')
            noun_after = (i+1 < len(out_labels) and out_labels[i+1] == 'N')
            if not (the_before or noun_after):
                out_labels[i] = 'm5'   # ordinal تنها → m5 (قید)
                changed = True

    return out_words, out_labels, out_numtype, changed


# =============================================================================
# ۵. قوانین مربوط به m5 (Ordinal alone / Adverbial ordinal)
# =============================================================================
def apply_m5_rules(out_words, out_labels, out_numtype, ctx):
    """
    قوانین اختصاصی برای برچسب m5 (ordinal numbers without determiner):
    - اعداد ترتیبی که به تنهایی آمده‌اند (بدون "the" و بدون اسم)
    - در این حالت نقش قیدی دارند (مثل: He came first)
    """
    changed = False

    for i in range(len(out_words)):
        if out_labels[i] != 'm5':
            continue

        # m5 ها در واقع adv هستند، بنابراین برچسب را adv می‌کنیم
        # اما برای حفظ تمایز، می‌توانیم آنها را به عنوان adv با یک ویژگی خاص نگه داریم
        # در اینجا به سادگی adv می‌کنیم، اما می‌توانید یک برچسب خاص مثل 'm5' نگه دارید
        out_labels[i] = 'adv'
        changed = True

    return out_words, out_labels, out_numtype, changed


# =============================================================================
# تابع کمکی: تشخیص اسم غیرقابل شمارش (برای قانون little)
# =============================================================================
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
# تابع اصلی برای اعمال همه‌ی قوانین به ترتیب
# =============================================================================
def apply_all_rules(out_words, out_labels, out_numtype, ctx):
    """
    اجرای تمام قوانین اختصاصی هر برچسب به ترتیب.
    هر قانون، خروجی خود را به قانون بعدی می‌دهد.
    """
    # ۱. قوانین m1
    out_words, out_labels, out_numtype, changed1 = apply_m1_rules(out_words, out_labels, out_numtype, ctx)
    
    # ۲. قوانین m2
    out_words, out_labels, out_numtype, changed2 = apply_m2_rules(out_words, out_labels, out_numtype, ctx)
    
    # ۳. قوانین m3
    out_words, out_labels, out_numtype, changed3 = apply_m3_rules(out_words, out_labels, out_numtype, ctx)
    
    # ۴. قوانین m4
    out_words, out_labels, out_numtype, changed4 = apply_m4_rules(out_words, out_labels, out_numtype, ctx)
    
    # ۵. قوانین m5
    out_words, out_labels, out_numtype, changed5 = apply_m5_rules(out_words, out_labels, out_numtype, ctx)

    # برگرداندن خروجی نهایی
    return out_words, out_labels, out_numtype
