import sys
import os
import logging
from src.utils import setup_nltk, read_text_file, save_text_file, ensure_dir, get_project_root, setup_logging
from src.processor import process_text

def main():
    setup_logging(level=logging.INFO)
    if len(sys.argv) < 2:
        logging.error("لطفاً مسیر فایل ورودی را مشخص کنید.")
        print("نحوه استفاده: python main.py <مسیر_فایل_ورودی>")
        sys.exit(1)

    input_path = sys.argv[1]
    setup_nltk()
    text = read_text_file(input_path)

    root = get_project_root()
    excel_path = os.path.join(root, "Book1.xlsx")
    if not os.path.exists(excel_path):
        logging.error(f"فایل '{excel_path}' پیدا نشد!")
        sys.exit(1)

    ensure_dir("data/output")
    output_excel = "data/output/output.xlsx"
    output_txt = "data/output/output.txt"

    logging.info("در حال پردازش متن...")
    df = process_text(text, excel_file=excel_path, output_file=output_excel)

    summary = f"تعداد کل کلمات پردازش‌شده: {len(df)}\nبرچسب‌ها:\n{df['برچسب'].value_counts().to_string()}"
    save_text_file(output_txt, summary)

    logging.info(f"✅ پردازش کامل شد! خروجی‌ها در پوشه‌ی 'data/output/' ذخیره شدند.")

if __name__ == "__main__":
    main()
