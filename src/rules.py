# =============================================================================
# rules.py - قوانین اختصاصی m1 تا m5
# =============================================================================

import re
from nltk.corpus import wordnet as wn
from src.utils import is_possessive_or_s, is_np_boundary, number_type, syllable_count, is_uncountable_noun

def apply_m1_rules(out_words, out_labels, out_numtype, ctx):
    changed = False
    phrases_set = ctx.get('phrases_set', set())
    simple_set = ctx.get('simple_set', set())
    compound_set = ctx.get('compound_set', set())
    cardinal_numbers = ctx.get('cardinal_numbers', set())
    ordinal_numbers = ctx.get('ordinal_numbers', set())

    # some + عدد → adv (به جز ترکیبات خاص)
    for i in range(len(out_words) - 1):
        if out_words[i].lower() == 'some' and out_labels[i] == 'm1':
            next_word = out_words[i + 1]
            if number_type(next_word, cardinal_numbers, ordinal_numbers):
                lookahead = ' '.join(out_words[i:i+6]).lower()
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

    # دو m1 پشت سر هم → دومی را adv کن
    for i in range(1, len(out_words)):
        if out_labels[i - 1] == 'm1' and out_labels[i] == 'm1':
            prev = out_words[i - 1].lower()
            cur = out_words[i].lower()
            if cur in compound_set or ' ' in out_words[i]:
                continue
            if prev in {'a', 'an'} and cur in {'lot', 'few', 'number', 'great many'}:
                continue
            out_labels[i] = 'adv'
            changed = True

    # m1 بعد از اسم (بدون "of") → adv یا m4
    for i in range(1, len(out_words)):
        if out_labels[i] != 'm1':
            continue
        current_word = out_words[i]
        current_lower = current_word.lower()
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
                out_labels[i] = 'm4'
            else:
                out_labels[i] = 'adv'
            changed = True

    return out_words, out_labels, out_numtype, changed

def apply_m2_rules(out_words, out_labels, out_numtype, ctx):
    changed = False
    for i in range(len(out_words) - 1):
        if out_words[i].lower() in ['more', 'most'] and out_labels[i] in ['m1', 'adv']:
            next_word = out_words[i + 1]
            if out_labels[i + 1] == 'm2' and syllable_count(next_word) > 1:
                out_labels[i] = 'm2'
                changed = True
    for i in range(len(out_words) - 1):
        if out_words[i].lower() == 'little' and out_labels[i] == 'm1':
            next_word = out_words[i + 1]
            if out_labels[i + 1] == 'N':
                if not is_uncountable_noun(next_word, ctx):
                    out_labels[i] = 'm2'
                    changed = True
    for i in range(len(out_words)):
        if '-' in out_words[i] and out_labels[i] == '':
            parts = out_words[i].split('-')
            if len(parts) >= 2:
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

def apply_m3_rules(out_words, out_labels, out_numtype, ctx):
    changed = False
    possessive_pronouns = {'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs'}
    for i in range(len(out_words)):
        if out_words[i].lower() in possessive_pronouns and out_labels[i] in ['', 'm1']:
            out_labels[i] = 'm3'
            changed = True
    return out_words, out_labels, out_numtype, changed

def apply_m4_rules(out_words, out_labels, out_numtype, ctx):
    changed = False
    ordinal_numbers = ctx.get('ordinal_numbers', set())
    for i in range(len(out_words)):
        if out_labels[i] != 'm4':
            continue
        if i > 0 and out_labels[i - 1] == 'N':
            if out_numtype[i] in ['cardinal', 'ordinal']:
                continue
            else:
                out_labels[i] = 'adv'
                changed = True
        if out_numtype[i] == 'ordinal':
            the_before = (i > 0 and out_words[i-1].lower() == 'the')
            noun_after = (i+1 < len(out_labels) and out_labels[i+1] == 'N')
            if not (the_before or noun_after):
                out_labels[i] = 'm5'
                changed = True
    return out_words, out_labels, out_numtype, changed

def apply_m5_rules(out_words, out_labels, out_numtype, ctx):
    changed = False
    for i in range(len(out_words)):
        if out_labels[i] == 'm5':
            out_labels[i] = 'adv'
            changed = True
    return out_words, out_labels, out_numtype, changed

def apply_all_rules(out_words, out_labels, out_numtype, ctx):
    out_words, out_labels, out_numtype, _ = apply_m1_rules(out_words, out_labels, out_numtype, ctx)
    out_words, out_labels, out_numtype, _ = apply_m2_rules(out_words, out_labels, out_numtype, ctx)
    out_words, out_labels, out_numtype, _ = apply_m3_rules(out_words, out_labels, out_numtype, ctx)
    out_words, out_labels, out_numtype, _ = apply_m4_rules(out_words, out_labels, out_numtype, ctx)
    out_words, out_labels, out_numtype, _ = apply_m5_rules(out_words, out_labels, out_numtype, ctx)
    return out_words, out_labels, out_numtype
