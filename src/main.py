import sys
import os
import logging

from src.utils import (
    setup_nltk, read_text_file, save_text_file,
    ensure_dir, get_project_root, setup_logging,
)
from src.core.pipeline import Pipeline


def main():
    setup_logging(level=logging.INFO)

    if len(sys.argv) < 2:
        logging.error("لطفاً مسیر فایل ورودی را مشخص کنید.")
        print("نحوه استفاده: python src/main.py <مسیر_فایل_ورودی>")
        sys.exit(1)

    input_path = sys.argv[1]

    # اطمینان از آماده بودن NLTK
    setup_nltk()

    text = read_text_file(input_path)

    # مسیر Book1.xlsx نسبت به ریشهٔ پروژه (سازگار با Docker)
    root = get_project_root()
    excel_path = os.path.join(root, "Book1.xlsx")
    if not os.path.exists(excel_path):
        logging.error(f"فایل '{excel_path}' پیدا نشد!")
        sys.exit(1)

    # مسیرهای خروجی مطلق (نسبت به ریشهٔ پروژه)
    output_dir = os.path.join(root, "data", "output")
    ensure_dir(output_dir)
    output_excel = os.path.join(output_dir, "output.xlsx")
    output_txt   = os.path.join(output_dir, "output.txt")

    # 🆕 استفاده از Pipeline مستقیم
    logging.info("در حال پردازش متن با Pipeline...")
    pipe = Pipeline(excel_file=excel_path)
    df = pipe.run(text, output_file=output_excel)

    # خلاصه
    summary = (
        f"تعداد کل کلمات پردازش‌شده: {len(df)}\n"
        f"برچسب‌ها:\n{df['برچسب'].value_counts().to_string()}"
    )
    save_text_file(output_txt, summary)

    logging.info(f"✅ پردازش کامل شد! خروجی‌ها در '{output_dir}/' ذخیره شدند.")


if __name__ == "__main__":
    main()
