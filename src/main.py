import sys
import os
import pandas as pd
from processor import process_text

def main():
    # بررسی تعداد آرگومان‌ها
    if len(sys.argv) < 2:
        print("نحوه استفاده: python main.py <مسیر_فایل_ورودی>")
        print("مثال: python main.py data/input/sample.txt")
        sys.exit(1)

    input_path = sys.argv[1]
    
    # بررسی وجود فایل ورودی
    if not os.path.exists(input_path):
        print(f"خطا: فایل '{input_path}' پیدا نشد!")
        sys.exit(1)

    # خواندن فایل ورودی
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # مسیر فایل اکسل (همون Book1.xlsx که باید کنار پروژه باشه)
    excel_path = 'Book1.xlsx'
    if not os.path.exists(excel_path):
        print(f"خطا: فایل '{excel_path}' پیدا نشد! لطفاً آن را در کنار اسکریپت قرار دهید.")
        sys.exit(1)

    # مسیر خروجی
    output_path = 'data/output/output.xlsx'
    
    # ایجاد پوشه خروجی اگر وجود ندارد
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # پردازش
    print("در حال پردازش متن...")
    df = process_text(text, excel_file=excel_path, output_file=output_path)
    
    # همچنین یک خروجی متنی ساده هم بسازیم
    with open('data/output/output.txt', 'w', encoding='utf-8') as f:
        f.write(f"تعداد کل کلمات پردازش‌شده: {len(df)}\n")
        f.write("برچسب‌ها:\n")
        f.write(df['برچسب'].value_counts().to_string())
    
    print(f"✅ پردازش کامل شد! خروجی‌ها در پوشه 'data/output/' ذخیره شدند.")
    print(f"📁 فایل اکسل: {output_path}")
    print(f"📁 فایل متنی: data/output/output.txt")

if __name__ == "__main__":
    main()
