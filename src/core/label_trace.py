"""
Label / rule conflict audit.

Default report is CONFLICT-ONLY:
  - label OVERRIDE (non-empty → different non-empty) by a later rule
  - oscillation loops (A→B→A… between two rules)

Seed / SET / CLEAR / merge index-shift noise is NOT listed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.ht_token import Token

_WATCH = ("label", "subtype", "role", "locked", "np_inner", "np_of_np")


def _snap(tok: Token) -> Dict[str, Any]:
    d = {k: getattr(tok, k) for k in _WATCH}
    d["word"] = tok.word
    return d


def _empty(v: Any) -> bool:
    return v in ("", None, "unknown", False)


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
        self._label_hist: Dict[Tuple[int, str], List[Tuple[str, str]]] = {}

    def clear(self) -> None:
        self.events.clear()
        self._step = 0
        self._last_setter.clear()
        self._label_hist.clear()

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
            self._label_hist.clear()
            return 1

        n_override = 0
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
                key = (i, tok.word)
                self._label_hist.setdefault(key, []).append((rule_name, new_lab))
                continue

            if not _empty(old_lab) and _empty(new_lab):
                self._last_setter.pop((i, "label"), None)
                continue

            prev_rule = self._last_setter.get((i, "label"), "?")
            self._step += 1
            self.events.append(
                TraceEvent(
                    step=self._step,
                    phase=phase,
                    rule=rule_name,
                    token_index=i,
                    word=tok.word,
                    changes=[
                        FieldChange(
                            field="label",
                            old=str(old_lab),
                            new=str(new_lab),
                            kind="OVERRIDE",
                        )
                    ],
                    prev_rule=prev_rule,
                )
            )
            self._last_setter[(i, "label")] = rule_name
            key = (i, tok.word)
            self._label_hist.setdefault(key, []).append((rule_name, new_lab))
            n_override += 1

        return n_override

    def override_events(self) -> List[TraceEvent]:
        return list(self.events)

    def oscillation_loops(self) -> List[str]:
        lines = []
        for (idx, word), hist in self._label_hist.items():
            if len(hist) < 4:
                continue
            labels = [h[1] for h in hist]
            uniq = list(dict.fromkeys(labels))
            if len(uniq) != 2:
                continue
            lines.append(
                f"  [{idx}] {word!r}: "
                f"{' → '.join(f'{r}({lb})' for r, lb in hist)} "
                f"  ⚠ loop between {uniq[0]!r} and {uniq[1]!r}"
            )
        return lines

    def format_text_report(
        self,
        tokens: List[Token],
        source_name: str = "",
    ) -> str:
        lines: List[str] = []
        lines.append("=" * 72)
        lines.append("LABEL CONFLICTS ONLY (OVERRIDE)")
        if source_name:
            lines.append(f"Source: {source_name}")
        lines.append(
            f"Tokens: {len(tokens)}  |  real overrides: {len(self.events)}"
        )
        lines.append("=" * 72)
        lines.append("")
        lines.append(
            "Only cases where a non-empty label was replaced by a different "
            "non-empty label."
        )
        lines.append("Seed / SET / CLEAR / merge shifts are omitted on purpose.")
        lines.append("")

        lines.append("## Overrides")
        lines.append("-" * 72)
        if not self.events:
            lines.append("(none)")
        else:
            for e in self.events:
                c = e.changes[0]
                lines.append(
                    f"  [{e.token_index}] {e.word!r}: "
                    f"{c.old!r} → {c.new!r}"
                    f"  by {e.rule}@{e.phase}"
                    f"  (was set by {e.prev_rule or '?'})"
                )

        loops = self.oscillation_loops()
        lines.append("")
        lines.append("## Oscillation loops (rules fighting each other)")
        lines.append("-" * 72)
        if not loops:
            lines.append("(none)")
        else:
            lines.extend(loops)

        lines.append("")
        lines.append("## How to read")
        lines.append(
            "  m2 → adv by rule_X (was set by rule_Y)\n"
            "  → rule_Y put m2, then rule_X overwrote it to adv.\n"
            "  Fix: change priority, add lock, or narrow the later rule."
        )
        lines.append("=" * 72)
        return "\n".join(lines) + "\n"

    def to_events_dataframe(self) -> pd.DataFrame:
        rows = []
        for e in self.events:
            for c in e.changes:
                rows.append(
                    {
                        "step": e.step,
                        "phase": e.phase,
                        "rule": e.rule,
                        "prev_rule": e.prev_rule,
                        "token_index": e.token_index,
                        "word": e.word,
                        "old_label": c.old,
                        "new_label": c.new,
                        "kind": c.kind,
                    }
                )
        if not rows:
            return pd.DataFrame(
                columns=[
                    "step",
                    "phase",
                    "rule",
                    "prev_rule",
                    "token_index",
                    "word",
                    "old_label",
                    "new_label",
                    "kind",
                ]
            )
        return pd.DataFrame(rows)

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
            df = self.to_events_dataframe()
            summary = []
            by_tok: Dict[Tuple[int, str], List[TraceEvent]] = {}
            for e in self.events:
                by_tok.setdefault((e.token_index, e.word), []).append(e)
            for (idx, word), evs in sorted(by_tok.items()):
                path = " → ".join(
                    f"{e.prev_rule}({e.changes[0].old})→{e.rule}({e.changes[0].new})"
                    for e in evs
                )
                summary.append(
                    {
                        "index": idx,
                        "word": word,
                        "override_count": len(evs),
                        "path": path,
                    }
                )
            summary_df = pd.DataFrame(summary)
            with pd.ExcelWriter(path_xlsx, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="overrides", index=False)
                summary_df.to_excel(writer, sheet_name="by_token", index=False)
