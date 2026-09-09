# =============================================================================
# utils.py
# توابع کمکی و عمومی برای کل پروژه (مدیریت فایل، تنظیمات NLTK، لاگینگ و ...)
# =============================================================================

import os
import sys
import logging
import nltk
from pathlib import Path


# =============================================================================
# ۱. تنظیمات اولیه NLTK (بررسی وجود دیتاها و دانلود در صورت نیاز)
# =============================================================================
def setup_nltk():
    """
    بررسی می‌کند که دیتاهای مورد نیاز NLTK (punkt, wordnet, cmudict) 
    از قبل نصب هستند یا نه. اگر نباشند، دانلود می‌کند.
    این تابع در محیط‌هایی که دیتاها از قبل در داکر وجود دارند، 
    کاری انجام نمی‌دهد و فقط یک پیام لاگ می‌دهد.
    """
    required_packages = ['punkt', 'wordnet', 'cmudict']
    missing_packages = []

    for package in required_packages:
        try:
            # بررسی وجود پکیج با استفاده از nltk.data.find
            nltk.data.find(f'tokenizers/{package}' if package == 'punkt' else f'corpora/{package}')
        except LookupError:
            missing_packages.append(package)

    if missing_packages:
        logging.info(f"دیتاهای NLTK زیر پیدا نشدند، در حال دانلود: {', '.join(missing_packages)}")
        for package in missing_packages:
            nltk.download(package, quiet=True)
        logging.info("دانلود دیتاهای NLTK کامل شد.")
    else:
        logging.info("تمامی دیتاهای مورد نیاز NLTK از قبل موجود هستند.")


# =============================================================================
# ۲. مدیریت فایل و مسیرها
# =============================================================================
def ensure_dir(path):
    """
    پوشه‌ی مورد نظر را می‌سازد (اگر وجود نداشته باشد).
    معادل os.makedirs(path, exist_ok=True) با پیام لاگ.
    """
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        logging.info(f"پوشه ساخته شد: {path}")
    else:
        logging.debug(f"پوشه از قبل وجود دارد: {path}")
    return path


def get_project_root():
    """
    مسیر ریشه‌ی پروژه را بر اساس مکان این فایل (utils.py) برمی‌گرداند.
    فرض می‌کند که این فایل در src/ قرار دارد، بنابراین ریشه یک سطح بالاتر است.
    """
    current_file = Path(__file__).resolve()
    return current_file.parent.parent  # یک سطح بالاتر از src/


def read_text_file(file_path):
    """
    یک فایل متنی را با encoding=utf-8 خوانده و محتوای آن را برمی‌گرداند.
    اگر فایل پیدا نشد، خطا را مدیریت کرده و برنامه را خاتمه می‌دهد.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logging.info(f"فایل ورودی با موفقیت خوانده شد: {file_path}")
        return content
    except FileNotFoundError:
        logging.error(f"فایل '{file_path}' پیدا نشد!")
        sys.exit(1)
    except Exception as e:
        logging.error(f"خطا در خواندن فایل '{file_path}': {e}")
        sys.exit(1)


def save_text_file(file_path, content):
    """
    یک فایل متنی را با encoding=utf-8 ذخیره می‌کند.
    قبل از ذخیره، اطمینان حاصل می‌کند که پوشه‌ی مقصد وجود دارد.
    """
    ensure_dir(os.path.dirname(file_path))
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"فایل خروجی متنی ذخیره شد: {file_path}")
    except Exception as e:
        logging.error(f"خطا در ذخیره‌ی فایل '{file_path}': {e}")
        sys.exit(1)


# =============================================================================
# ۳. تنظیمات لاگینگ (Logging)
# =============================================================================
def setup_logging(level=logging.INFO, log_file=None):
    """
    تنظیمات اولیه لاگینگ را انجام می‌دهد.
    - level: سطح لاگ (مثلاً logging.DEBUG برای دیباگ)
    - log_file: اگر آدرس یک فایل داده شود، لاگ‌ها در آن نیز ذخیره می‌شوند.
    """
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        ensure_dir(os.path.dirname(log_file))
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))

    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=handlers
    )
    logging.info("سیستم لاگینگ راه‌اندازی شد.")


# =============================================================================
# ۴. توابع کمکی عمومی (متفرقه)
# =============================================================================
def is_text_file(file_path):
    """
    تشخیص اینکه آیا فایل ورودی احتمالاً یک فایل متنی است یا نه.
    با بررسی پسوند (این یک تشخیص ساده است، برای موارد خاص نیاز به بررسی محتوا دارد).
    """
    text_extensions = {'.txt', '.text', '.md', '.rtf'}
    ext = Path(file_path).suffix.lower()
    return ext in text_extensions or not ext  # فایل‌های بدون پسوند را هم متن فرض می‌کنیم


def clean_text_for_processing(text):
    """
    پاکسازی اولیه‌ی متن قبل از ارسال به پردازشگر اصلی.
    شامل حذف فاصله‌های اضافی، تبدیل خطوط جدید به فاصله و ...
    """
    # جایگزینی خطوط جدید با فاصله
    text = text.replace('\n', ' ').replace('\r', ' ')
    # حذف فاصله‌های اضافی (بیش از یک فاصله)
    text = ' '.join(text.split())
    return text


def get_output_paths(base_dir="data/output", prefix="output"):
    """
    تولید مسیرهای پیش‌فرض برای فایل‌های خروجی (اکسل و متن).
    برمی‌گرداند: (path_excel, path_txt)
    """
    excel_path = os.path.join(base_dir, f"{prefix}.xlsx")
    txt_path = os.path.join(base_dir, f"{prefix}.txt")
    return excel_path, txt_path
