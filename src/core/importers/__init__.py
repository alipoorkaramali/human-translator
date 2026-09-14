"""Importers package — prefer explicit imports from submodules.

Lazy exports keep lightweight modules free of NLTK at import time.
"""

def __getattr__(name):
    if name in ("build_context", "load_excel", "load_nltk_data"):
        from . import data_importer
        return getattr(data_importer, name)
    if name in (
        "import_np_rules",
        "import_m1_rules",
        "import_m2_to_m5",
        "import_np_special_rules",
        "import_np_span_rules",
    ):
        from . import np_importer
        return getattr(np_importer, name)
    if name == "import_vp_rules":
        from . import vp_importer
        return getattr(vp_importer, name)
    if name == "import_special_rules":
        from . import special_checker
        return getattr(special_checker, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "build_context",
    "load_excel",
    "load_nltk_data",
    "import_np_rules",
    "import_vp_rules",
    "import_m1_rules",
    "import_m2_to_m5",
    "import_np_special_rules",
    "import_special_rules",
]
