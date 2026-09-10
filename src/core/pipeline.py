from .context import Context
from .processor import Processor
from .rule_base import RuleRegistry

from .importers.data_importer      import build_context
from .importers.m1_importer        import import_m1_rules
from .importers.m2_m5_importer     import import_m2_to_m5
from .importers.special_checker    import import_special_rules


class Pipeline:
    """
    ترتیب اجرا:
        1) DataImporter → Context
        2) M1Importer   → ثبت قوانین m1
        3) M2toM5Importer → ثبت m2..m5
        4) SpecialChecker → ثبت حالت‌های خاص
        5) Processor.run_all
    """

    def __init__(self, excel_file: str = 'Book1.xlsx',
                 nltk_data_path: str = None):
        # 1) داده
        self.ctx = build_context(excel_file, nltk_data_path)

        # 2) Registry
        self.registry = RuleRegistry()

        # 3) Importers
        import_m1_rules(self.registry)
        import_m2_to_m5(self.registry)
        import_special_rules(self.registry)

        # 4) Processor
        self.processor = Processor(self.ctx, self.registry)

    def run(self, text: str, output_file: str = None):
        from utils.text_utils import preprocess_text, tokenize_english

        text = preprocess_text(text)
        words = tokenize_english(text)

        self.processor.load(words)
        self.processor.run_all()

        if output_file:
            self.processor.save(output_file)
        return self.processor.to_dataframe()
