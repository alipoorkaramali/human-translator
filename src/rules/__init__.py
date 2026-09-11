"""
rules package.
ساختار:
  rules/np/   → m1..m5 + special  (Nominal Phrase)
  rules/vp/   → vp1..vp3 + special (Verbal Phrase)

تابع apply_all_rules برای سازگاری با کد قدیمی حفظ شده است.
"""
from src.core.context import Context
from src.core.rule_base import RuleRegistry
from src.core.processor import Processor


def apply_all_rules(out_words, out_labels, out_numtype, ctx):
    """
    Backward-compatible wrapper.
    ورودی: سه لیست موازی + dict/Context
    خروجی: سه لیست به‌روزرسانی‌شده
    """
    context = Context()
    if isinstance(ctx, dict):
        for k, v in ctx.items():
            if hasattr(context, k):
                setattr(context, k, v)
    else:
        context = ctx

    registry = RuleRegistry()
    from src.core.importers.np_importer import import_np_rules
    from src.core.importers.vp_importer import import_vp_rules
    import_np_rules(registry)
    import_vp_rules(registry)

    proc = Processor(context, registry)
    proc.load(out_words, out_labels, out_numtype)
    proc.run_all()

    return proc.words(), proc.labels(), proc.numtypes()
