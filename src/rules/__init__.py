"""
rules package.
تابع apply_all_rules را برای کدهای قدیمی حفظ می‌کند.
در پشت صحنه از RuleRegistry + 6 فاز استفاده می‌کند.
"""
from src.core.context import Context
from src.core.rule_base import RuleRegistry
from src.core.processor import Processor


def apply_all_rules(out_words, out_labels, out_numtype, ctx):
    """
    Backward-compatible wrapper.
    ورودی: سه لیست موازی + dict ctx
    خروجی: سه لیست به‌روزرسانی‌شده
    """
    # 1) Context بساز
    context = Context()
    if isinstance(ctx, dict):
        for k, v in ctx.items():
            if hasattr(context, k):
                setattr(context, k, v)
    else:
        context = ctx

    # 2) Registry + importers
    registry = RuleRegistry()
    from src.core.importers.m1_importer       import import_m1_rules
    from src.core.importers.m2_m5_importer    import import_m2_to_m5
    from src.core.importers.special_checker   import import_special_rules
    import_m1_rules(registry)
    import_m2_to_m5(registry)
    import_special_rules(registry)

    # 3) Processor
    proc = Processor(context, registry)
    proc.load(out_words, out_labels, out_numtype)
    proc.run_all()

    return proc.words(), proc.labels(), proc.numtypes()
