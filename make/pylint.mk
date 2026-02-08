# =============================================================================
## CATEGORY: Pylint - Python Code Analysis
# КОМАНДЫ ДЛЯ ПРОВЕРКИ КАЧЕСТВА PYTHON КОДА
# =============================================================================

PYTHON_FILES := $(shell find . -name "*.py" \
	-not -path "./venv/*" \
	-not -path "./.venv/*" \
	-not -path "./env/*" \
	-not -path "./.env/*" \
	-not -path "./build/*" \
	-not -path "./dist/*" \
	-not -path "./.git/*" \
	-not -path "./__pycache__/*" \
	-not -path "./*.egg-info/*" \
	-not -path "./node_modules/*")

PYLINT := $(shell command -v pylint 2> /dev/null)
PYLINT_SCORE ?= 7.0
PYLINT_RC_FILE ?= .pylintrc

# -----------------------------------------------------------------------------
# ОСНОВНЫЕ КОМАНДЫ
# -----------------------------------------------------------------------------

pylint-check: ## Проверить все Python файлы
	@echo "🔍 Проверка качества кода..."
ifeq ($(PYLINT),)
	@echo "❌ Pylint не установлен!"
	@exit 1
else
	@echo "📊 Запуск Pylint..."
	@pylint $(PYTHON_FILES) || true
	@echo "✅ Проверка завершена!"
endif

pylint-score: ## Проверить с минимальным порогом оценки
	@echo "🎯 Проверка с порогом $(PYLINT_SCORE)..."
ifeq ($(PYLINT),)
	@echo "❌ Pylint не установлен!"
	@exit 1
else
	@pylint --fail-under=$(PYLINT_SCORE) $(PYTHON_FILES) || \
		(echo "❌ Оценка ниже порога $(PYLINT_SCORE)!"; exit 1)
	@echo "✅ Оценка выше $(PYLINT_SCORE)!"
endif

pylint-errors-only: ## Показать только ошибки
	@echo "🚨 Проверка только ошибок..."
ifeq ($(PYLINT),)
	@echo "❌ Pylint не установлен!"
	@exit 1
else
	@pylint --errors-only $(PYTHON_FILES) || true
endif

pylint-verbose: ## Подробный вывод
	@echo "📋 Подробная проверка..."
ifeq ($(PYLINT),)
	@echo "❌ Pylint не установлен!"
	@exit 1
else
	@pylint --verbose $(PYTHON_FILES) || true
endif

# -----------------------------------------------------------------------------
# РАБОТА С ФАЙЛАМИ И ПАПКАМИ
# -----------------------------------------------------------------------------

pylint-file: ## Проверить конкретный файл (FILE=path.py)
ifeq ($(PYLINT),)
	@echo "❌ Pylint не установлен!"
	@exit 1
else ifeq ($(FILE),)
	@echo "❌ Укажите файл: make pylint-file FILE=path.py"
	@exit 1
else ifneq ($(wildcard $(FILE)),)
	@echo "📄 Проверка файла: $(FILE)"
	@pylint $(FILE)
else
	@echo "❌ Файл не найден: $(FILE)"
	@exit 1
endif

pylint-dir: ## Проверить папку (DIR=path/)
ifeq ($(PYLINT),)
	@echo "❌ Pylint не установлен!"
	@exit 1
else ifeq ($(DIR),)
	@echo "❌ Укажите папку: make pylint-dir DIR=path/"
	@exit 1
else ifneq ($(wildcard $(DIR)),)
	@echo "📁 Проверка папки: $(DIR)"
	@find $(DIR) -name "*.py" -exec pylint {} \; || true
	@echo "✅ Проверка папки завершена!"
else
	@echo "❌ Папка не найдена: $(DIR)"
	@exit 1
endif

# -----------------------------------------------------------------------------
# КОНФИГУРАЦИЯ
# -----------------------------------------------------------------------------

pylint-config: ## Показать конфигурацию
	@echo "⚙️  Конфигурация Pylint:"
	@echo "  Минимальный порог: $(PYLINT_SCORE)"
	@echo "  Конфиг файл: $(PYLINT_RC_FILE)"
	@echo "  Файлов для проверки: $$(echo "$(PYTHON_FILES)" | wc -w | tr -d ' ')"

pylint-version: ## Показать версию
	@echo "ℹ️  Информация о Pylint:"
ifeq ($(PYLINT),)
	@echo "❌ Pylint не установлен!"
else
	@pylint --version
endif

pylint-generate-config: ## Сгенерировать конфигурационный файл
	@echo "📝 Генерация конфигурационного файла..."
ifeq ($(PYLINT),)
	@echo "❌ Pylint не установлен!"
	@exit 1
else
	@pylint --generate-rcfile > $(PYLINT_RC_FILE) 2>/dev/null || true
	@echo "✅ Конфигурационный файл создан: $(PYLINT_RC_FILE)"
endif

# -----------------------------------------------------------------------------
# ПРЕСЕТЫ И ФИЛЬТРЫ
# -----------------------------------------------------------------------------

pylint-strict: ## Строгая проверка (порог 9.0)
	@echo "📏 Строгая проверка (порог 9.0)..."
	@PYLINT_SCORE=9.0 $(MAKE) pylint-score

pylint-moderate: ## Умеренная проверка (порог 7.0)
	@echo "⚖️  Умеренная проверка (порог 7.0)..."
	@PYLINT_SCORE=7.0 $(MAKE) pylint-score

pylint-relaxed: ## Щадящая проверка (порог 5.0)
	@echo "😌 Щадящая проверка (порог 5.0)..."
	@PYLINT_SCORE=5.0 $(MAKE) pylint-score

# -----------------------------------------------------------------------------
# УСТАНОВКА
# -----------------------------------------------------------------------------

install-pylint: ## Установить или обновить Pylint
	@echo "📦 Установка Pylint..."
	@pip install --upgrade pylint
	@echo "✅ Pylint установлен!"
	@pylint --version

# -----------------------------------------------------------------------------
# PHONY ЦЕЛИ
# -----------------------------------------------------------------------------
.PHONY: pylint-check pylint-score pylint-errors-only pylint-verbose \
	pylint-file pylint-dir pylint-config pylint-version \
	pylint-generate-config pylint-strict pylint-moderate pylint-relaxed \
	install-pylint
