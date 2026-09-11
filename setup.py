from setuptools import setup, find_packages
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# ---------- خواندن README با ایمنی ----------
_readme_path = _HERE / "README.md"
_long_description = (
    _readme_path.read_text(encoding="utf-8")
    if _readme_path.exists()
    else "ابزار برچسب‌زنی کمیت‌نماها، اعداد، صفات و قیود در زبان انگلیسی."
)

setup(
    name="human-translator",
    version="2.0.0",
    author="Ali Poorkaramali",
    author_email="alipoorkaramali@example.com",   # ← ایمیل واقعی خود را بگذارید
    description="ابزار برچسب‌زنی کمیت‌نماها، اعداد، صفات و قیود در زبان انگلیسی",
    long_description=_long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alipoorkaramali/human-translator",

    # ---------- پکیج ----------
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        # اگر روزی Book1.xlsx را داخل پکیج گذاشتی
        "": ["*.xlsx", "*.txt"],
    },

    # ---------- وابستگی‌ها ----------
    install_requires=[
        "pandas>=2.0,<3.0",
        "nltk>=3.8,<4.0",
        "openpyxl>=3.1,<4.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "pytest-xdist>=3.3",
            "pytest-mock>=3.10",
            "black>=23.0",
            "isort>=5.12",
            "flake8>=6.0",
            "pylint>=2.17",
            "mypy>=1.0",
        ],
        "jupyter": [
            "ipywidgets>=8.0",
            "jupyter>=1.0",
        ],
    },

    # ---------- CLI ----------
    entry_points={
        "console_scripts": [
            "human-translator = main:main",
        ],
    },

    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Natural Language :: Persian",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="nlp pos-tagging quantifier determiner wordnet nltk persian english",
)
