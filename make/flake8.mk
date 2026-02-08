# =============================================================================
## CATEGORY: Flake8 - Python Linter
# КОМАНДЫ ДЛЯ ПРОВЕРКИ СТИЛЯ И КАЧЕСТВА КОДА
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

FLAKE8 := $(shell command -v flake8 2> /dev/null)
FLAKE8_CONFIG ?= .flake8
FLAKE8_MAX_LINE_LENGTH ?= 100
FLAKE8_MAX_COMPLEXITY ?= 10

# -----------------------------------------------------------------------------
# ОСНОВНЫЕ КОМАНДЫ
# -----------------------------------------------------------------------------

flake8-check: ## Проверить все Python файлы
	@echo "🔍 Проверка кода Flake8..."
ifeq ($(FLAKE8),)
	@echo "❌ Flake8 не установлен!"
	@exit 1
else
	@flake8 $(PYTHON_FILES) || true
	@echo "✅ Проверка завершена!"
endif

flake8-strict: ## Строгая проверка (выход при первой ошибке)
	@echo "📏 Строгая проверка..."
ifeq ($(FLAKE8),)
	@echo "❌ Flake8 не установлен!"
	@exit 1
else
	@flake8 --exit-zero $(PYTHON_FILES) || \
		(echo "❌ Найдены ошибки!"; exit 1)
endif

flake8-statistics: ## Показать статистику ошибок
	@echo "📊 Статистика Flake8..."
ifeq ($(FLAKE8),)
	@echo "❌ Flake8 не установлен!"
	@exit 1
else
	@flake8 --statistics $(PYTHON_FILES) || true
endif

flake8-verbose: ## Подробный вывод
	@echo "📋 Подробная проверка..."
ifeq ($(FLAKE8),)
	@echo "❌ Flake8 не установлен!"
	@exit 1
else
	@flake8 --verbose $(PYTHON_FILES) || true
endif

# -----------------------------------------------------------------------------
# РАБОТА С ФАЙЛАМИ И ПАПКАМИ
# -----------------------------------------------------------------------------

flake8-file: ## Проверить конкретный файл (FILE=path.py)
ifeq ($(FLAKE8),)
	@echo "❌ Flake8 не установлен!"
	@exit 1
else ifeq ($(FILE),)
	@echo "❌ Укажите файл: make flake8-file FILE=path.py"
	@exit 1
else ifneq ($(wildcard $(FILE)),)
	@echo "📄 Проверка файла: $(FILE)"
	@flake8 $(FILE)
else
	@echo "❌ Файл не найден: $(FILE)"
	@exit 1
endif

flake8-dir: ## Проверить папку (DIR=path/)
ifeq ($(FLAKE8),)
	@echo "❌ Flake8 не установлен!"
	@exit 1
else ifeq ($(DIR),)
	@echo "❌ Укажите папку: make flake8-dir DIR=path/"
	@exit 1
else ifneq ($(wildcard $(DIR)),)
	@echo "📁 Проверка папки: $(DIR)"
	@flake8 $(DIR) || true
	@echo "✅ Проверка папки завершена!"
else
	@echo "❌ Папка не найдена: $(DIR)"
	@exit 1
endif

# -----------------------------------------------------------------------------
# КОНФИГУРАЦИЯ И ФИЛЬТРЫ
# -----------------------------------------------------------------------------

flake8-config: ## Показать конфигурацию
	@echo "⚙️  Конфигурация Flake8:"
	@echo "  Конфиг файл: $(FLAKE8_CONFIG)"
	@echo "  Макс. длина строки: $(FLAKE8_MAX_LINE_LENGTH)"
	@echo "  Макс. сложность: $(FLAKE8_MAX_COMPLEXITY)"
	@echo "  Файлов для проверки: $$(echo "$(PYTHON_FILES)" | wc -w | tr -d ' ')"

flake8-version: ## Показать версию
	@echo "ℹ️  Информация о Flake8:"
ifeq ($(FLAKE8),)
	@echo "❌ Flake8 не установлен!"
else
	@flake8 --version
endif

flake8-show-config: ## Показать текущую конфигурацию
	@echo "🔧 Текущая конфигурация Flake8:"
ifeq ($(FLAKE8),)
	@echo "❌ Flake8 не установлен!"
	@exit 1
else
	@flake8 --show-config || true
endif

# -----------------------------------------------------------------------------
# ПРЕСЕТЫ И НАСТРОЙКИ
# -----------------------------------------------------------------------------

flake8-pep8: ## Проверка только PEP 8
	@echo "📐 Проверка PEP 8..."
ifeq ($(FLAKE8),)
	@echo "❌ Flake8 не установлен!"
	@exit 1
else
	@flake8 --select=E,W $(PYTHON_FILES) || true
endif

flake8-pyflakes: ## Проверка только PyFlakes (логические ошибки)
	@echo "🤔 Проверка PyFlakes..."
ifeq ($(FLAKE8),)
	@echo "❌ Flake8 не установлен!"
	@exit 1
else
	@flake8 --select=F $(PYTHON_FILES) || true
endif

flake8-mccabe: ## Проверка сложности кода (McCabe)
	@echo "🌀 Проверка сложности кода..."
ifeq ($(FLAKE8),)
	@echo "❌ Flake8 не установлен!"
	@exit 1
else
	@flake8 --max-complexity=$(FLAKE8_MAX_COMPLEXITY) $(PYTHON_FILES) || true
endif

# -----------------------------------------------------------------------------
# ПАРАМЕТРЫ ПРОВЕРКИ
# -----------------------------------------------------------------------------

flake8-line-length-79: ## Проверка по PEP 8 (79 символов)
	@echo "📐 PEP 8 проверка (79 символов)..."
	@FLAKE8_MAX_LINE_LENGTH=79 $(MAKE) flake8-check

flake8-line-length-100: ## Современная проверка (100 символов)
	@echo "💎 Современная проверка (100 символов)..."
	@FLAKE8_MAX_LINE_LENGTH=100 $(MAKE) flake8-check

flake8-line-length-120: ## Проверка с длинными строками (120 символов)
	@echo "📏 Проверка с длинными строками (120 символов)..."
	@FLAKE8_MAX_LINE_LENGTH=120 $(MAKE) flake8-check

flake8-complexity-5: ## Проверка со сложностью 5
	@echo "🧮 Проверка сложности 5..."
	@FLAKE8_MAX_COMPLEXITY=5 $(MAKE) flake8-check

flake8-complexity-15: ## Проверка со сложностью 15
	@echo "🧮 Проверка сложности 15..."
	@FLAKE8_MAX_COMPLEXITY=15 $(MAKE) flake8-check

# -----------------------------------------------------------------------------
# УСТАНОВКА
# -----------------------------------------------------------------------------

install-flake8: ## Установить или обновить Flake8
	@echo "📦 Установка Flake8..."
	@pip install --upgrade flake8
	@echo "✅ Flake8 установлен!"
	@flake8 --version

# -----------------------------------------------------------------------------
# PHONY ЦЕЛИ
# -----------------------------------------------------------------------------
.PHONY: flake8-check flake8-strict flake8-statistics flake8-verbose \
	flake8-file flake8-dir flake8-config flake8-version flake8-show-config \
	flake8-pep8 flake8-pyflakes flake8-mccabe \
	flake8-line-length-79 flake8-line-length-100 flake8-line-length-120 \
	flake8-complexity-5 flake8-complexity-15 \
	install-flake8
