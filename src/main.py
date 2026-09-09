import sys
import os
import logging
from utils import (
    setup_nltk, ensure_dir, read_text_file, save_text_file,
    clean_text_for_processing, get_output_paths, get_project_root
)
from processor import process_text

def main():
    # ۱. تنظیم لاگینگ
    from utils import setup_logging
    setup_logging(level=logging.INFO)

    # ۲. بررسی آرگومان ورودی
    if len(sys.argv) < 2:
        logging.error("لطفاً مسیر فایل ورودی را مشخص کنید.")
        print("نحوه استفاده: python main.py <مسیر_فایل_ورودی>")
        print("مثال: python main.py data/input/sample.txt")
        sys.exit(1)

    input_path = sys.argv[1]

    # ۳. تنظیم NLTK (اگر داده‌ها موجود نباشند دانلود می‌کند)
    setup_nltk()

    # ۴. خواندن فایل ورودی
    text = read_text_file(input_path)

    # ۵. پاکسازی اولیه‌ی متن
    text = clean_text_for_processing(text)

    # ۶. مسیر فایل اکسل (Book1.xlsx) در ریشه‌ی پروژه
    root = get_project_root()
    excel_path = os.path.join(root, "Book1.xlsx")
    if not os.path.exists(excel_path):
        logging.error(f"فایل '{excel_path}' پیدا نشد! لطفاً آن را در ریشه‌ی پروژه قرار دهید.")
        sys.exit(1)

    # ۷. مسیرهای خروجی
    output_excel, output_txt = get_output_paths()

    # ۸. پردازش متن
    logging.info("در حال پردازش متن...")
    df = process_text(text, excel_file=excel_path, output_file=output_excel)

    # ۹. ذخیره‌ی خروجی متنی ساده
    summary = f"تعداد کل کلمات پردازش‌شده: {len(df)}\n"
    summary += "برچسب‌ها:\n"
    summary += df['برچسب'].value_counts().to_string()
    save_text_file(output_txt, summary)

    logging.info(f"✅ پردازش کامل شد! خروجی‌ها در پوشه‌ی 'data/output/' ذخیره شدند.")
    logging.info(f"📁 فایل اکسل: {output_excel}")
    logging.info(f"📁 فایل متنی: {output_txt}")

if __name__ == "__main__":
    main()
