"""
Label / rule audit trail.

Records every field change a rule makes on tokens so conflicts and
multi-step tagging paths are visible in output_*_trace.txt / .xlsx.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from src.ht_token import Token

_WATCH = ("label", "subtype", "role", "locked", "np_inner", "np_of_np")


def _snap(tok: Token) -> Dict[str, Any]:
    return {k: getattr(tok, k) for k in _WATCH}


def _classify(field: str, old: Any, new: Any) -> str:
    if field == "locked":
        if (not old) and new:
            return "LOCK"
        if old and (not new):
            return "UNLOCK"
        return "CHANGE"
    old_empty = old in ("", None, "unknown", False)
    new_empty = new in ("", None, "unknown", False)
    if old_empty and not new_empty:
        return "SET"
    if (not old_empty) and new_empty:
        return "CLEAR"
    if old != new:
        if field == "label":
            return "OVERRIDE"
        return "CHANGE"
    return "SAME"


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

    def summary_line(self) -> str:
        parts = []
        for c in self.changes:
            parts.append(f"{c.field}: {c.old!r} → {c.new!r} [{c.kind}]")
        return "; ".join(parts)


class LabelTracer:
    def __init__(self) -> None:
        self.events: List[TraceEvent] = []
        self._step = 0
        self.enabled = True

    def clear(self) -> None:
        self.events.clear()
        self._step = 0

    def record_rule(
        self,
        phase: str,
        rule_name: str,
        tokens: List[Token],
        before: List[Dict[str, Any]],
    ) -> int:
        if not self.enabled:
            return 0
        n_changed = 0
        for i, tok in enumerate(tokens):
            after = _snap(tok)
            prev = before[i] if i < len(before) else {}
            changes: List[FieldChange] = []
            for key in _WATCH:
                old, new = prev.get(key), after.get(key)
                if old == new:
                    continue
                kind = _classify(key, old, new)
                changes.append(
                    FieldChange(
                        field=key,
                        old="" if old is None else str(old),
                        new="" if new is None else str(new),
                        kind=kind,
                    )
                )
            if not changes:
                continue
            n_changed += 1
            self._step += 1
            self.events.append(
                TraceEvent(
                    step=self._step,
                    phase=phase,
                    rule=rule_name,
                    token_index=i,
                    word=tok.word,
                    changes=changes,
                )
            )
        return n_changed

    @staticmethod
    def snapshot(tokens: List[Token]) -> List[Dict[str, Any]]:
        return [_snap(t) for t in tokens]

    def events_for_token(self, index: int) -> List[TraceEvent]:
        return [e for e in self.events if e.token_index == index]

    def override_events(self) -> List[TraceEvent]:
        return [
            e
            for e in self.events
            if any(c.kind == "OVERRIDE" for c in e.changes)
        ]

    def multi_label_tokens(self) -> List[int]:
        counts: Dict[int, int] = {}
        for e in self.events:
            if any(c.field == "label" for c in e.changes):
                counts[e.token_index] = counts.get(e.token_index, 0) + 1
        return sorted(i for i, n in counts.items() if n > 1)

    def to_events_dataframe(self) -> pd.DataFrame:
        rows = []
        for e in self.events:
            for c in e.changes:
                rows.append(
                    {
                        "step": e.step,
                        "phase": e.phase,
                        "rule": e.rule,
                        "token_index": e.token_index,
                        "word": e.word,
                        "field": c.field,
                        "old": c.old,
                        "new": c.new,
                        "kind": c.kind,
                    }
                )
        if not rows:
            return pd.DataFrame(
                columns=[
                    "step",
                    "phase",
                    "rule",
                    "token_index",
                    "word",
                    "field",
                    "old",
                    "new",
                    "kind",
                ]
            )
        return pd.DataFrame(rows)

    def format_text_report(
        self,
        tokens: List[Token],
        source_name: str = "",
    ) -> str:
        lines: List[str] = []
        lines.append("=" * 72)
        lines.append("LABEL TRACE / مسیر برچسب‌گذاری")
        if source_name:
            lines.append(f"Source: {source_name}")
        lines.append(f"Tokens: {len(tokens)}  |  Events: {len(self.events)}")
        lines.append("=" * 72)

        lines.append("")
        lines.append("## 1) Chronological rule applications (changes only)")
        lines.append("-" * 72)
        if not self.events:
            lines.append("(no field changes recorded)")
        for e in self.events:
            lines.append(
                f"[{e.step:04d}] phase={e.phase:<12} rule={e.rule:<28} "
                f"token[{e.token_index}]='{e.word}'"
            )
            for c in e.changes:
                lines.append(
                    f"         {c.field}: {c.old!r} → {c.new!r}  [{c.kind}]"
                )

        lines.append("")
        lines.append("## 2) Per-token path (full history)")
        lines.append("-" * 72)
        for i, tok in enumerate(tokens):
            evs = self.events_for_token(i)
            st = f"/{tok.subtype}" if tok.subtype else ""
            lines.append(
                f"### [{i}] {tok.word!r}  final: label={tok.label or '∅'}{st}  "
                f"role={tok.role}  locked={tok.locked}"
            )
            if tok.np_inner or tok.np_of_np:
                lines.append(
                    f"      spans: np_inner={tok.np_inner!r}  "
                    f"np_of_np={tok.np_of_np!r}"
                )
            if not evs:
                lines.append("      (no rule changed this token)")
                continue
            label_steps = 0
            for e in evs:
                label_steps += sum(1 for c in e.changes if c.field == "label")
                lines.append(
                    f"      → #{e.step} {e.rule}@{e.phase}: {e.summary_line()}"
                )
            if label_steps > 1:
                lines.append(
                    f"      ⚠ label changed {label_steps} times "
                    f"(possible rule interaction / override)"
                )

        multi = self.multi_label_tokens()
        lines.append("")
        lines.append("## 3) Tokens with multiple label assignments")
        lines.append("-" * 72)
        if not multi:
            lines.append("(none — each token's label set at most once)")
        else:
            for i in multi:
                evs = [
                    e
                    for e in self.events_for_token(i)
                    if any(c.field == "label" for c in e.changes)
                ]
                path = " → ".join(
                    f"{e.rule}("
                    f"{next(c.new for c in e.changes if c.field == 'label')})"
                    for e in evs
                )
                lines.append(f"  [{i}] {tokens[i].word!r}: {path}")

        overrides = self.override_events()
        lines.append("")
        lines.append("## 4) Overrides (label replaced by another rule)")
        lines.append("-" * 72)
        if not overrides:
            lines.append("(none)")
        else:
            for e in overrides:
                for c in e.changes:
                    if c.kind != "OVERRIDE":
                        continue
                    prev_rules = []
                    for pe in self.events:
                        if pe.step >= e.step:
                            break
                        if pe.token_index != e.token_index:
                            continue
                        for pc in pe.changes:
                            if pc.field == c.field and pc.new == c.old:
                                prev_rules.append(pe.rule)
                    prev = prev_rules[-1] if prev_rules else "?"
                    lines.append(
                        f"  [{e.token_index}] {e.word!r} {c.field}: "
                        f"{c.old!r} → {c.new!r}  by {e.rule}@{e.phase} "
                        f"(was set by {prev})"
                    )

        lines.append("")
        lines.append("## 5) Legend")
        lines.append(
            "  SET      first non-empty value\n"
            "  OVERRIDE non-empty replaced by a different value (conflict risk)\n"
            "  CHANGE   other field change\n"
            "  CLEAR    value removed\n"
            "  LOCK     token locked\n"
        )
        lines.append("=" * 72)
        return "\n".join(lines) + "\n"

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
            summary_rows = []
            for i, tok in enumerate(tokens):
                evs = self.events_for_token(i)
                label_path = []
                rules = []
                for e in evs:
                    rules.append(e.rule)
                    for c in e.changes:
                        if c.field == "label":
                            label_path.append(
                                f"{c.old or '∅'}→{c.new or '∅'}@{e.rule}"
                            )
                summary_rows.append(
                    {
                        "index": i,
                        "word": tok.word,
                        "final_label": tok.label,
                        "final_subtype": tok.subtype,
                        "final_role": tok.role,
                        "label_path": " | ".join(label_path) if label_path else "",
                        "rules_involved": " → ".join(dict.fromkeys(rules)),
                        "label_change_count": sum(
                            1
                            for e in evs
                            for c in e.changes
                            if c.field == "label"
                        ),
                        "had_override": any(
                            c.kind == "OVERRIDE"
                            for e in evs
                            for c in e.changes
                        ),
                    }
                )
            summary_df = pd.DataFrame(summary_rows)
            with pd.ExcelWriter(path_xlsx, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="events", index=False)
                summary_df.to_excel(writer, sheet_name="per_token", index=False)
