# =============================================================================
# processor.py - پردازشگر اصلی
# =============================================================================

import pandas as pd
import nltk
import re
from nltk.corpus import wordnet as wn
from nltk.corpus import cmudict

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

def possessive_before_index(out_words, idx, max_lookback=15):
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
    fractions = {'half','halves','third','thirds','quarter','quarters','fourth','fourths',
                 'fifth','fifths','sixth','seventh','eighth','ninth','tenth'}
    if i+4 < len(tokens) and tokens[i+1].lower() == 'and' and tokens[i+2].lower() in cardinals2 and \
       tokens[i+4].lower().rstrip('s') in fractions:
        return " ".join(tokens[i:i+5]), i+5, True
    return None, i, False

def apply_law_sh_fixed(out_words, out_labels, out_numtype, ctx):
    singular_heads = {"number", "amount", "kind", "type", "sort", "deal", "pile", "bunch", "bit",
                      "set", "group", "variety", "lot", "sum", "many", "quantity"}
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
        if (k < len(out_words) and out_words[k].lower() in singular_heads and 
            k+1 < len(out_words) and out_words[k+1].lower() == 'of'):
            combined = " ".join(out_words[start:k+2])
            out_words[start:k+2] = [combined]
            out_labels[start:k+2] = ['m1']
            out_numtype[start:k+2] = ['']
            i = start + 1
        else:
            i += 1

def apply_law_z_fixed(out_words, out_labels, out_numtype, ctx):
    plural_heads = {"numbers", "amounts", "kinds", "types", "sorts", "groups", "varieties",
                    "bunches", "piles", "bits", "sets", "lots", "ranges", "series", "volumes",
                    "heaps", "loads", "tons", "dozens", "scores", "myriads", "multitudes"}
    vague_quant_set = ctx.get('vague_quant_set', set())
    i = 0
    while i < len(out_words) - 1:
        start = i
        np_boundary = i
        while np_boundary < len(out_words):
            if is_np_boundary(out_words[np_boundary]):
                np_boundary += 1
                break
            np_boundary += 1
        possessive_exists_in_np = any(is_possessive_or_s(out_words[j]) for j in range(i, np_boundary))
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
            if label in ['m2', 'adv'] or (label == '' and wn.synsets(word_low) and wn.synsets(word_low)[0].pos() in 'as') or word_low in vague_quant_set or label == 'm1':
                modifier_end += 1
                continue
            break
        head_idx = modifier_end
        of_idx = modifier_end + 1
        if (head_idx >= len(out_words) or out_words[head_idx].lower() not in plural_heads or
            of_idx >= len(out_words) or out_words[of_idx].lower() != 'of'):
            i = start + 1
            continue
        if of_idx + 1 < len(out_words):
            next_w = out_words[of_idx + 1].lower()
            if wn.synsets(next_w) and wn.synsets(next_w)[0].pos() == 'v':
                i = start + 1
                continue
        if modifier_end == start or has_real_m1:
            i = of_idx + 1 if has_real_m1 else start + 1
            continue
        combined = " ".join(out_words[start:of_idx + 1])
        out_words[start:of_idx + 1] = [combined]
        out_labels[start:of_idx + 1] = ['m1']
        out_numtype[start:of_idx + 1] = ['']
        i = start + 1

def apply_the_ordinal_rule(out_words, out_labels, out_numtype):
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
            out_words[i] = combined
            out_labels[i] = 'm1'
            out_numtype[i] = 'ordinal'
            del out_words[i + 1]
            del out_labels[i + 1]
            del out_numtype[i + 1]
        else:
            out_labels[i + 1] = 'adv'
            i += 1

def _final_fix_quantifier_after_noun(out_words, out_labels, out_numtype):
    for i in range(1, len(out_words)):
        if out_labels[i] != 'm1':
            continue
        current_lower = out_words[i].lower()
        if current_lower in {'a', 'an', 'the', 'this', 'that', 'these', 'those'}:
            continue
        is_number = out_numtype[i] in ['cardinal', 'ordinal']
        has_noun_without_of = False
        for j in range(i-1, -1, -1):
            if is_np_boundary(out_words[j]) or out_words[j].lower() == 'of':
                break
            if out_labels[j] == 'N':
                has_noun_without_of = True
                break
        if has_noun_without_of:
            out_labels[i] = 'm4' if is_number else 'adv'

def apply_wordnet_and_final_rules(out_words, out_labels, out_numtype, ctx):
    dict_roles = [''] * len(out_words)
    for i, (w, lab) in enumerate(zip(out_words, out_labels)):
        wl = w.lower()
        if lab:
            continue
        syns = wn.synsets(wl)
        if not syns:
            continue
        pos = syns[0].pos()
        if pos == 'n':
            out_labels[i] = 'N'
            dict_roles[i] = 'noun'
        elif pos in ('a', 's'):
            out_labels[i] = 'm2'
            dict_roles[i] = 'adjective'
        elif pos == 'v':
            out_labels[i] = 'V'
            dict_roles[i] = 'verb'
        elif pos == 'r':
            out_labels[i] = 'adv'
            dict_roles[i] = 'adverb'
    # little / a little rules
    for i in range(len(out_words)):
        current_word = out_words[i].lower()
        if current_word in ('a little', 'little') and i + 1 < len(out_words) and out_labels[i + 1] == 'N':
            next_noun = out_words[i + 1]
            if current_word == 'a little':
                out_labels[i] = 'm1'
                dict_roles[i] = 'determiner/quantifier'
            elif is_uncountable_noun(next_noun, ctx):
                out_labels[i] = 'm1'
                dict_roles[i] = 'determiner/quantifier'
            else:
                out_labels[i] = 'm2'
                dict_roles[i] = 'adjective'
    for i in range(len(out_words)):
        if out_words[i].lower() == 'enough' and i > 0 and out_labels[i - 1] == 'm2':
            out_labels[i] = 'adv'
            dict_roles[i] = 'adverb'
    return out_words, out_labels, out_numtype, dict_roles

def postprocess(out_words, out_labels, out_numtype, ctx):
    max_iterations = 8
    for _ in range(max_iterations):
        changed = False
        for i in range(len(out_words) - 1):
            if out_words[i].lower() == 'some' and out_labels[i] != 'adv':
                next_word = out_words[i + 1]
                if number_type(next_word, ctx['cardinal_numbers'], ctx['ordinal_numbers']):
                    lookahead = ' '.join(out_words[i:i+6]).lower()
                    if any(lookahead.startswith(p) for p in ['some hundred', 'some thousand', 'some dozen', 'some score']) or \
                       any(x in lookahead for x in ['some hundreds', 'some thousands', 'some dozens']):
                        continue
                    if any(comp in lookahead for comp in ctx.get('compound_set', set()) if comp.startswith('some ')):
                        continue
                    out_labels[i] = 'adv'
                    changed = True
        apply_law_sh_fixed(out_words, out_labels, out_numtype, ctx)
        apply_law_z_fixed(out_words, out_labels, out_numtype, ctx)
        apply_the_ordinal_rule(out_words, out_labels, out_numtype)
        _final_fix_quantifier_after_noun(out_words, out_labels, out_numtype)
        if not changed:
            break
    out_words, out_labels, out_numtype, dict_roles = apply_wordnet_and_final_rules(out_words, out_labels, out_numtype, ctx)
    return out_words, out_labels, out_numtype, dict_roles

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

        # Multi-word phrases from phrases_set (up to 5 words)
        found = False
        for length in range(min(5, len(tokens) - i), 0, -1):
            phrase = ' '.join(tokens[i:i+length]).lower()
            if phrase in phrases_set or phrase in compound_set or phrase in simple_set:
                out_words.append(' '.join(tokens[i:i+length]))
                out_labels.append('m1')
                out_numtype.append(nt or '')
                i += length
                found = True
                break
        if found:
            continue

        # Numbers
        if nt:
            out_words.append(w)
            out_labels.append('m1')
            out_numtype.append(nt)
            i += 1
            continue

        # Possessives
        if is_possessive_or_s(w):
            out_words.append(w)
            out_labels.append('m3')
            out_numtype.append('')
            i += 1
            continue

        # Intensifiers
        if wl in intensifier_set:
            out_words.append(w)
            out_labels.append('adv')
            out_numtype.append('')
            i += 1
            continue

        # Default
        out_words.append(w)
        out_labels.append('m1' if wl in phrases_set else '')
        out_numtype.append('')

        if re.search(r"['’]s$|s'$", w, re.I):
            base = re.sub(r"['’]s$|s'$", "", w.lower())
            syns = wn.synsets(base)
            if syns and syns[0].pos() == 'n':
                out_labels[-1] = 'N'
            elif out_labels[-1] != 'm1':
                out_labels[-1] = 'N'
        i += 1

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
