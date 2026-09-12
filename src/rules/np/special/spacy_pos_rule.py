"""
برچسب‌زنی POS با spaCy (بافت‌محور) به‌جای WordNet syns[0].

نگاشت:
  NOUN/PROPN → N
  VERB/AUX   → V
  ADJ        → m2
  ADV        → adv

برچسب‌های rule-based محافظت می‌شوند: m1, m3, m4 و توکن‌های چندکلمه‌ای.
"""
from typing import List, Optional, TYPE_CHECKING
import logging

from src.core.rule_base import Rule

if TYPE_CHECKING:
    from src.ht_token import Token
    from src.core.context import Context

logger = logging.getLogger(__name__)

_NLP = None
_NLP_FAILED = False

_POS_TO_LABEL = {
    "NOUN": "N",
    "PROPN": "N",
    "VERB": "V",
    "AUX": "V",
    "ADJ": "m2",
    "ADV": "adv",
}
_POS_TO_ROLE = {
    "NOUN": "noun",
    "PROPN": "proper noun",
    "VERB": "verb",
    "AUX": "auxiliary verb",
    "ADJ": "adjective",
    "ADV": "adverb",
    "DET": "determiner",
    "PRON": "pronoun",
    "ADP": "preposition",
    "CCONJ": "conjunction",
    "SCONJ": "conjunction",
    "PART": "particle",
    "NUM": "numeral",
    "PUNCT": "punctuation",
}

_PROTECTED_LABELS = {"m1", "m3", "m4"}


def _get_nlp():
    """بارگذاری تنبل مدل؛ یک‌بار در حافظه."""
    global _NLP, _NLP_FAILED
    if _NLP is not None or _NLP_FAILED:
        return _NLP
    try:
        import spacy
        try:
            _NLP = spacy.load("en_core_web_sm")
        except OSError:
            logger.info("دانلود مدل en_core_web_sm …")
            from spacy.cli import download
            download("en_core_web_sm")
            _NLP = spacy.load("en_core_web_sm")
        return _NLP
    except Exception as e:
        logger.warning("spaCy در دسترس نیست (%s) — POS از spaCy رد می‌شود.", e)
        _NLP_FAILED = True
        return None


def _align_pos(tokens: List["Token"], doc) -> List[Optional[str]]:
    """
    هم‌ترازی حریصانهٔ توکن‌های ما با توکن‌های spaCy.
    برای توکن چندکلمه‌ای: None (دست نزن).
    """
    result: List[Optional[str]] = [None] * len(tokens)
    spacy_i = 0
    spacy_toks = list(doc)

    for i, tok in enumerate(tokens):
        w = tok.word
        if " " in w:
            # چندکلمه: تعداد تقریبی توکن spaCy را رد کن
            parts = w.split()
            for _ in parts:
                if spacy_i < len(spacy_toks):
                    spacy_i += 1
            continue

        # رد کردن فاصله‌مانند در spaCy
        while spacy_i < len(spacy_toks) and spacy_toks[spacy_i].is_space:
            spacy_i += 1

        if spacy_i >= len(spacy_toks):
            break

        st = spacy_toks[spacy_i]
        if st.text.lower() == w.lower() or st.text == w:
            result[i] = st.pos_
            spacy_i += 1
        else:
            # جستجوی محدود جلوتر
            found = False
            for j in range(spacy_i, min(spacy_i + 3, len(spacy_toks))):
                if spacy_toks[j].text.lower() == w.lower():
                    result[i] = spacy_toks[j].pos_
                    spacy_i = j + 1
                    found = True
                    break
            if not found:
                # تک‌کلمه به spaCy
                try:
                    d2 = st.doc.vocab  # noqa — fallback زیر
                except Exception:
                    pass
                spacy_i += 1

    return result


class SpacyPosRule(Rule):
    name = "spacy_pos"
    target_label = "special"
    priority = 86  # قبل از wordnet (88) و little (90)

    def apply(self, tokens: List["Token"], ctx: "Context") -> bool:
        if not tokens:
            return False

        nlp = getattr(ctx, "spacy_nlp", None) or _get_nlp()
        if nlp is None:
            return False

        # ذخیره روی ctx برای استفادهٔ بعدی در همان Pipeline
        if getattr(ctx, "spacy_nlp", None) is None:
            try:
                ctx.extra["spacy_nlp"] = nlp
            except Exception:
                pass

        text = " ".join(t.word for t in tokens)
        try:
            doc = nlp(text)
        except Exception as e:
            logger.warning("spaCy nlp() failed: %s", e)
            return False

        poses = _align_pos(tokens, doc)
        changed = False

        for i, tok in enumerate(tokens):
            if tok.locked:
                continue
            if " " in tok.word:
                continue
            if tok.label in _PROTECTED_LABELS:
                # فقط role را اگر خالی است از spaCy پر کن
                pos = poses[i]
                if pos and tok.role in ("", "unknown"):
                    role = _POS_TO_ROLE.get(pos)
                    if role:
                        tok.role = role
                        changed = True
                continue

            pos = poses[i]
            if not pos:
                continue

            new_label = _POS_TO_LABEL.get(pos)
            new_role = _POS_TO_ROLE.get(pos)

            if new_label and tok.label in ("", "N", "V", "m2", "adv"):
                if tok.label != new_label:
                    tok.label = new_label
                    changed = True
            if new_role and tok.role in ("", "unknown"):
                tok.role = new_role
                changed = True
            elif new_role and new_label and tok.label == new_label:
                if tok.role != new_role and tok.role in (
                    "", "unknown", "noun", "verb", "adjective", "adverb"
                ):
                    tok.role = new_role
                    changed = True

            # DET/ADP بدون برچسب ساختاری ما
            if pos == "ADP" and tok.label == "":
                if tok.role != "preposition":
                    tok.role = "preposition"
                    changed = True
            if pos == "DET" and tok.label == "" and tok.word.lower() not in {
                "a", "an", "the", "this", "that", "these", "those"
            }:
                if tok.role in ("", "unknown"):
                    tok.role = "determiner"
                    changed = True

        return changed
