from setuptools import setup, find_packages

setup(
    name="human-translator",
    version="1.0.0",
    author="نام شما",
    author_email="ایمیل شما",
    description="ابزار برچسب‌زنی کمیت‌نماها، اعداد، صفات و قیود در زبان انگلیسی",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/username/human-translator",  # آدرس مخزن خودت رو بذار
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas",
        "nltk",
        "openpyxl"
    ],
    entry_points={
        "console_scripts": [
            "human-translator = main:main",  # بعد از نصب، با دستور human-translator اجرا میشه
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
