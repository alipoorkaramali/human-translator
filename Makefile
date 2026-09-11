# ============================================================
# Makefile برای پروژهی human-translator
# ============================================================

# ----------------------------------------
# متغیرها
# ----------------------------------------
IMAGE_NAME   = text-processor
CONTAINER    = text-processor-run
DOCKERFILE   = docker/Dockerfile
INPUT_FILE   = data/input/sample.txt

# ----------------------------------------
# پیشفرض: help
# ----------------------------------------
.PHONY: help
help:
	@echo "------------------------------------------------------------------"
	@echo "  📦 پروژهی human-translator - دستورات موجود:"
	@echo "------------------------------------------------------------------"
	@echo "  --- داکر ---"
	@echo "  make build              :  ساخت ایمیج داکر"
	@echo "  make run                :  اجرای برنامه با sample.txt"
	@echo "  make run-file FILE=...  :  اجرا با فایل دلخواه"
	@echo "  make shell              :  ورود به شل کانتینر"
	@echo "  make clean              :  حذف ایمیج"
	@echo "  --- توسعه ---"
	@echo "  make install-dev        :  نصب وابستگیهای توسعه"
	@echo "  make format             :  فرمت با black + isort"
	@echo "  make lint               :  بررسی با flake8"
	@echo "  --- تست ---"
	@echo "  make test               :  اجرای همه تستها"
	@echo "  make test-core          :  تستهای Core"
	@echo "  make test-importers     :  تستهای Importers"
	@echo "  make test-rules         :  تستهای Rules"
	@echo "  make coverage           :  گزارش پوشش تست (HTML)"
	@echo "  make check              :  lint + test (قبل از push)"
	@echo "------------------------------------------------------------------"

# ============================================================
# داکر
# ============================================================
.PHONY: build
build:
	@echo "🚀 در حال ساخت ایمیج $(IMAGE_NAME) ..."
	docker build -f $(DOCKERFILE) -t $(IMAGE_NAME) .
	@echo "✅ ایمیج ساخته شد!"

.PHONY: run
run:
	@echo "🚀 اجرا با $(INPUT_FILE) ..."
	docker run --rm \
		-v "$(CURDIR)/data:/app/data" \
		-v "$(CURDIR)/Book1.xlsx:/app/Book1.xlsx" \
		$(IMAGE_NAME) $(INPUT_FILE)
	@echo "✅ خروجی در data/output/."

.PHONY: run-file
run-file:
ifndef FILE
	$(error "FILE را مشخص کنید! مثال: make run-file FILE=data/input/mytext.txt")
endif
	@echo "🚀 اجرا با $(FILE) ..."
	docker run --rm \
		-v "$(CURDIR)/data:/app/data" \
		-v "$(CURDIR)/Book1.xlsx:/app/Book1.xlsx" \
		$(IMAGE_NAME) $(FILE)
	@echo "✅ خروجی در data/output/."

.PHONY: shell
shell:
	@echo "🐚 ورود به شل کانتینر ..."
	docker run --rm -it \
		-v "$(CURDIR)/data:/app/data" \
		-v "$(CURDIR)/Book1.xlsx:/app/Book1.xlsx" \
		--entrypoint /bin/bash \
		$(IMAGE_NAME)

.PHONY: clean
clean:
	@echo "🧹 حذف ایمیج $(IMAGE_NAME) ..."
	docker rmi $(IMAGE_NAME) || echo "✅ ایمیج وجود نداشت."

# ============================================================
# توسعه
# ============================================================
.PHONY: install-dev
install-dev:
	@echo "📦 نصب وابستگیهای توسعه ..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "✅ نصب کامل شد."

.PHONY: format
format:
	@echo "🎨 فرمت کردن کدها ..."
	black src/ tests/ scripts/
	isort src/ tests/ scripts/
	@echo "✅ فرمت کامل شد."

.PHONY: lint
lint:
	@echo "🔍 بررسی با flake8 ..."
	flake8 src/ tests/ scripts/ --max-line-length=127 --statistics
	@echo "✅ بررسی کامل شد."

# ============================================================
# تست
# ============================================================
.PHONY: test
test:
	@echo "🧪 اجرای همه تستها ..."
	PYTHONPATH=. pytest tests/ -v

.PHONY: test-core
test-core:
	@echo "🧪 تستهای Core ..."
	PYTHONPATH=. pytest tests/test_core/ -v

.PHONY: test-importers
test-importers:
	@echo "🧪 تستهای Importers ..."
	PYTHONPATH=. pytest tests/test_importers/ -v

.PHONY: test-rules
test-rules:
	@echo "🧪 تستهای Rules ..."
	PYTHONPATH=. pytest tests/test_rules/ -v

.PHONY: coverage
coverage:
	@echo "📊 محاسبه پوشش تست ..."
	PYTHONPATH=. pytest tests/ \
		--cov=src \
		--cov-report=term-missing \
		--cov-report=html
	@echo "✅ گزارش HTML در htmlcov/."

.PHONY: check
check: lint test
	@echo "✅ همه بررسیها موفق."
