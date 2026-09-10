#!/usr/bin/env python3
# =============================================================================
# scripts/download_nltk.py
# دانلود دیتاهای NLTK مورد نیاز پروژه human-translator
#
# استفاده:
#   python scripts/download_nltk.py
#   NLTK_DATA=/usr/share/nltk_data python scripts/download_nltk.py
# =============================================================================

import os
import sys
import zipfile
import logging
from pathlib import Path

import nltk

# ------------------------- تنظیمات -------------------------
PACKAGES = [
    ("punkt",     "tokenizers"),
    ("wordnet",   "corpora"),
    ("cmudict",   "corpora"),
    ("omw-1.4",   "corpora"),
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger("nltk_downloader")


# ------------------------- مسیر NLTK -------------------------
def resolve_nltk_dir() -> str:
    """
    مسیر NLTK_DATA را برمی‌گرداند.
    اولویت:
        1) env var NLTK_DATA
        2) ./nltk_data در ریشهٔ پروژه
        3) /usr/share/nltk_data
    """
    env_path = os.environ.get("NLTK_DATA")
    if env_path:
        return env_path

    project_root = Path(__file__).resolve().parent.parent
    local_path = project_root / "nltk_data"
    if local_path.exists() or os.access(project_root, os.W_OK):
        return str(local_path)

    return "/usr/share/nltk_data"


# ------------------------- بررسی وجود پکیج -------------------------
def is_downloaded(pkg: str, subdir: str, base_dir: str) -> bool:
    """چک می‌کند پکیج در مسیر داده‌شده موجود است یا نه."""
    p = Path(base_dir) / subdir / pkg
    return p.exists()


# ------------------------- استخراج wordnet -------------------------
def ensure_wordnet_extracted(base_dir: str) -> None:
    """اگر wordnet.zip هست ولی wordnet/ نیست، استخراج کن."""
    corpora = Path(base_dir) / "corpora"
    zip_path = corpora / "wordnet.zip"
    dir_path = corpora / "wordnet"

    if zip_path.exists() and not dir_path.exists():
        log.info(f"استخراج {zip_path} ...")
        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(corpora)
            log.info("✅ wordnet استخراج شد.")
        except Exception as e:
            log.error(f"❌ استخراج wordnet ناموفق: {e}")
            raise


# ------------------------- دانلود اصلی -------------------------
def download_all(base_dir: str) -> int:
    """
    همهٔ پکیج‌های لازم را دانلود می‌کند.
    خروجی: تعداد پکیج‌های جدید دانلود‌شده
    """
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    log.info(f"📁 مسیر NLTK_DATA: {base_dir}")

    # اطمینان از حضور مسیر در nltk.data.path
    if base_dir not in nltk.data.path:
        nltk.data.path.insert(0, base_dir)

    downloaded = 0
    for pkg, subdir in PACKAGES:
        if is_downloaded(pkg, subdir, base_dir):
            log.info(f"✅ {pkg} از قبل موجود است.")
            continue

        log.info(f"⬇️  دانلود {pkg} ...")
        try:
            ok = nltk.download(pkg, download_dir=base_dir, quiet=True)
            if ok:
                downloaded += 1
                log.info(f"✅ {pkg} دانلود شد.")
            else:
                log.error(f"❌ دانلود {pkg} ناموفق بود.")
                return -1
        except Exception as e:
            log.error(f"❌ خطا در دانلود {pkg}: {e}")
            return -1

    # استخراج wordnet در صورت نیاز
    ensure_wordnet_extracted(base_dir)
    return downloaded


# ------------------------- main -------------------------
def main() -> int:
    base_dir = resolve_nltk_dir()
    try:
        n = download_all(base_dir)
        if n < 0:
            log.error("❌ دانلود ناقص ماند.")
            return 1
        if n == 0:
            log.info("🎉 همهٔ دیتاها از قبل موجود بودند.")
        else:
            log.info(f"🎉 {n} پکیج جدید دانلود شد.")
        return 0
    except Exception as e:
        log.exception(f"❌ خطای غیرمنتظره: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
