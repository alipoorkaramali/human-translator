# ============================================================
# Makefile برای پروژه‌ی human-translator
# شامل دستورات کوتاه برای ساخت و اجرا با داکر
# ============================================================

# ----------------------------------------
# متغیرهای اصلی (برای جلوگیری از تکرار)
# ----------------------------------------
IMAGE_NAME   = text-processor
CONTAINER    = text-processor-run
DOCKERFILE   = docker/Dockerfile
INPUT_FILE   = data/input/sample.txt

# ----------------------------------------
# دستورات پیش‌فرض (وقتی فقط 'make' می‌زنید)
# ----------------------------------------
.PHONY: help
help:
	@echo "------------------------------------------------------------------"
	@echo "  📦 پروژه‌ی human-translator - دستورات موجود:"
	@echo "------------------------------------------------------------------"
	@echo "  make build         :  ساخت ایمیج داکر"
	@echo "  make run           :  اجرای برنامه با فایل sample.txt"
	@echo "  make run-file FILE=... : اجرا با فایل ورودی دلخواه (مثال: make run-file FILE=data/input/mytext.txt)"
	@echo "  make clean         :  حذف ایمیج ساخته‌شده"
	@echo "  make shell         :  ورود به شل کانتینر برای دیباگ"
	@echo "  make install-dev   :  نصب وابستگی‌های توسعه روی سیستم میزبان"
	@echo "  make format        :  فرمت کردن خودکار کدهای پایتون (نیاز به black)"
	@echo "  make lint          :  بررسی خطاهای استایل کد (نیاز به flake8)"
	@echo "------------------------------------------------------------------"

# ----------------------------------------
# ساخت ایمیج داکر (با استفاده از Dockerfile)
# ----------------------------------------
.PHONY: build
build:
	@echo "🚀 در حال ساخت ایمیج $(IMAGE_NAME) ..."
	docker build -f $(DOCKERFILE) -t $(IMAGE_NAME) .
	@echo "✅ ایمیج با موفقیت ساخته شد!"

# ----------------------------------------
# اجرای برنامه با فایل نمونه (sample.txt)
# ----------------------------------------
.PHONY: run
run:
	@echo "🚀 در حال اجرا با فایل $(INPUT_FILE) ..."
	docker run --rm \
		-v "$(CURDIR)/data:/app/data" \
		-v "$(CURDIR)/Book1.xlsx:/app/Book1.xlsx" \
		$(IMAGE_NAME) $(INPUT_FILE)
	@echo "✅ اجرا کامل شد! خروجی را در data/output/ ببینید."

# ----------------------------------------
# اجرا با فایل ورودی دلخواه (مثال: make run-file FILE=data/input/other.txt)
# ----------------------------------------
.PHONY: run-file
run-file:
ifndef FILE
	$(error "FILE را مشخص کنید! مثال: make run-file FILE=data/input/mytext.txt")
endif
	@echo "🚀 در حال اجرا با فایل $(FILE) ..."
	docker run --rm \
		-v "$(CURDIR)/data:/app/data" \
		-v "$(CURDIR)/Book1.xlsx:/app/Book1.xlsx" \
		$(IMAGE_NAME) $(FILE)
	@echo "✅ اجرا کامل شد! خروجی را در data/output/ ببینید."

# ----------------------------------------
# ورود به شل (bash) داخل کانتینر (برای دیباگ)
# ----------------------------------------
.PHONY: shell
shell:
	@echo "🐚 در حال ورود به شل کانتینر ..."
	docker run --rm -it \
		-v "$(CURDIR)/data:/app/data" \
		-v "$(CURDIR)/Book1.xlsx:/app/Book1.xlsx" \
		--entrypoint /bin/bash \
		$(IMAGE_NAME)

# ----------------------------------------
# حذف ایمیج ساخته‌شده
# ----------------------------------------
.PHONY: clean
clean:
	@echo "🧹 در حال حذف ایمیج $(IMAGE_NAME) ..."
	docker rmi $(IMAGE_NAME) || echo "✅ ایمیج وجود نداشت یا حذف شد."

# ----------------------------------------
# نصب وابستگی‌های توسعه روی سیستم میزبان (اختیاری)
# ----------------------------------------
.PHONY: install-dev
install-dev:
	@echo "📦 در حال نصب وابستگی‌های توسعه ..."
	pip install -r requirements-dev.txt
	@echo "✅ نصب کامل شد."

# ----------------------------------------
# فرمت کردن خودکار کدها با black
# ----------------------------------------
.PHONY: format
format:
	@echo "🎨 در حال فرمت کردن کدها با black ..."
	black src/
	isort src/
	@echo "✅ فرمت کامل شد."

# ----------------------------------------
# بررسی خطاهای استایل با flake8
# ----------------------------------------
.PHONY: lint
lint:
	@echo "🔍 در حال بررسی کد با flake8 ..."
	flake8 src/
	@echo "✅ بررسی کامل شد (اگر خطایی بالا دیدید، باید رفع کنید)."
