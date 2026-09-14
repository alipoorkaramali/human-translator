"""
Conflict report for hand-written rules only.

Ignores automatic POS engines (spaCy, WordNet). Collapses oscillation
noise to one line per unique conflict. Seed / SET / CLEAR / merges omitted.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.ht_token import Token

_AUTO_RULES = frozenset({
    "spacy_pos",
    "wordnet_finalize",
    "seed",
})

_WATCH = ("label", "subtype", "role", "locked", "np_inner", "np_of_np")


def is_np_boundary(token) -> bool:
    """Same rules as src.utils.is_np_boundary (single source of truth)."""
    try:
        from src.utils import is_np_boundary as _real
        return _real(token)
    except Exception:
        if not token:
            return False
        if hasattr(token, "label") and getattr(token, "label", "") == "V":
            return True
        w = str(getattr(token, "word", token)).lower()
        if not w or " " in w:
            return False
        if w in {".", "!", "?", ";", ":", "—", ","}:
            return True
        if w in {
            "in", "on", "at", "to", "for", "from", "with", "by", "about",
            "and", "but", "or",
        }:
            return True
        return False


def _snap(tok: Token) -> Dict[str, Any]:
    d = {k: getattr(tok, k) for k in _WATCH}
    d["word"] = tok.word
    return d


def _empty(v: Any) -> bool:
    return v in ("", None, "unknown", False)


def _is_auto(name: str) -> bool:
    return (name or "") in _AUTO_RULES


def _np_span(tokens: List[Token], index: int) -> Tuple[int, int, str]:
    """NP window: after previous boundary → before next boundary."""
    if not tokens or index < 0 or index >= len(tokens):
        return index, index, ""

    left = index
    while left > 0 and not is_np_boundary(tokens[left - 1]):
        left -= 1

    right = index
    while right < len(tokens) - 1 and not is_np_boundary(tokens[right + 1]):
        right += 1

    pieces = []
    for i in range(left, right + 1):
        w = tokens[i].word
        pieces.append(f"[{w}]" if i == index else w)
    return left, right, " ".join(pieces)


@dataclass
class FieldChange:
    field: str
    old: str
    new: str
    kind: str


@dataclass
class TraceEvent:
    step: int
    phase: str
    rule: str
    token_index: int
    word: str
    changes: List[FieldChange] = field(default_factory=list)
    prev_rule: str = ""


class LabelTracer:
    def __init__(self) -> None:
        self.events: List[TraceEvent] = []
        self._step = 0
        self.enabled = True
        self._last_setter: Dict[Tuple[int, str], str] = {}
        self._raw_overrides: List[TraceEvent] = []

    def clear(self) -> None:
        self.events.clear()
        self._raw_overrides.clear()
        self._step = 0
        self._last_setter.clear()

    @staticmethod
    def snapshot(tokens: List[Token]) -> List[Dict[str, Any]]:
        return [_snap(t) for t in tokens]

    def record_rule(
        self,
        phase: str,
        rule_name: str,
        tokens: List[Token],
        before: List[Dict[str, Any]],
    ) -> int:
        if not self.enabled:
            return 0

        if len(before) != len(tokens):
            self._last_setter.clear()
            return 1

        n = 0
        for i, tok in enumerate(tokens):
            if i >= len(before):
                break
            prev = before[i]
            if prev.get("word") != tok.word:
                continue

            old_lab = prev.get("label") or ""
            new_lab = tok.label or ""
            if old_lab == new_lab:
                if new_lab and not _empty(new_lab):
                    self._last_setter[(i, "label")] = rule_name
                continue

            if _empty(old_lab) and not _empty(new_lab):
                self._last_setter[(i, "label")] = rule_name
                continue

            if not _empty(old_lab) and _empty(new_lab):
                self._last_setter.pop((i, "label"), None)
                continue

            prev_rule = self._last_setter.get((i, "label"), "?")
            self._step += 1
            ev = TraceEvent(
                step=self._step,
                phase=phase,
                rule=rule_name,
                token_index=i,
                word=tok.word,
                changes=[
                    FieldChange("label", str(old_lab), str(new_lab), "OVERRIDE")
                ],
                prev_rule=prev_rule,
            )
            self._raw_overrides.append(ev)
            if not _is_auto(rule_name):
                self.events.append(ev)
            self._last_setter[(i, "label")] = rule_name
            n += 1
        return n

    def _dedupe_hand_events(self) -> List[TraceEvent]:
        seen = set()
        out = []
        for e in self.events:
            c = e.changes[0]
            sig = (e.token_index, e.word, c.old, c.new, e.rule, e.prev_rule)
            if sig in seen:
                continue
            seen.add(sig)
            out.append(e)
        return out

    def format_text_report(
        self,
        tokens: List[Token],
        source_name: str = "",
    ) -> str:
        hand = self._dedupe_hand_events()
        lines: List[str] = []
        lines.append("=" * 64)
        lines.append("تداخل قوانین دست‌نویس")
        if source_name:
            lines.append(f"Source: {source_name}")
        lines.append(f"Tokens: {len(tokens)}  |  conflicts: {len(hand)}")
        lines.append("=" * 64)

        if not hand:
            lines.append("")
            lines.append("(none)")
            lines.append("=" * 64)
            return "\n".join(lines) + "\n"

        for n, e in enumerate(hand, 1):
            c = e.changes[0]
            lo, hi, np_text = _np_span(tokens, e.token_index)
            lines.append("")
            lines.append(f"--- تعارض {n} ---")
            lines.append(f"کلمه:  {e.word!r}  (جایگاه {e.token_index})")
            lines.append(f"برچسب: {c.old}  ←تغییر به→  {c.new}")
            lines.append(f"اول:   قانون {e.prev_rule!r}  برچسب {c.old!r} گذاشت")
            lines.append(f"بعد:   قانون {e.rule!r}  آن را به {c.new!r} عوض کرد")
            lines.append(f"فاز:   {e.phase}")
            lines.append(f"NP:    {np_text}")
            lines.append(f"       (توکن‌های {lo} … {hi})")

        lines.append("")
        lines.append("=" * 64)
        return "\n".join(lines) + "\n"

    def _rows_with_np(self, tokens: List[Token]) -> List[dict]:
        rows = []
        for e in self._dedupe_hand_events():
            c = e.changes[0]
            lo, hi, np_text = _np_span(tokens, e.token_index)
            rows.append(
                {
                    "token_index": e.token_index,
                    "word": e.word,
                    "old_label": c.old,
                    "new_label": c.new,
                    "prev_rule": e.prev_rule,
                    "rule": e.rule,
                    "phase": e.phase,
                    "np_from": lo,
                    "np_to": hi,
                    "np_text": np_text,
                }
            )
        return rows

    def save(
        self,
        tokens: List[Token],
        path_txt: str,
        path_xlsx: Optional[str] = None,
        source_name: str = "",
    ) -> None:
        text = self.format_text_report(tokens, source_name=source_name)
        with open(path_txt, "w", encoding="utf-8") as f:
            f.write(text)
        if path_xlsx:
            df = pd.DataFrame(
                self._rows_with_np(tokens),
                columns=[
                    "token_index",
                    "word",
                    "old_label",
                    "new_label",
                    "prev_rule",
                    "rule",
                    "phase",
                    "np_from",
                    "np_to",
                    "np_text",
                ],
            )
            with pd.ExcelWriter(path_xlsx, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="conflicts", index=False)
