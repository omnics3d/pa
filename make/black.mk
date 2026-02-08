# =============================================================================
## CATEGORY: Black - Python Code Formatting
# КОМАНДЫ ДЛЯ ФОРМАТИРОВАНИЯ PYTHON КОДА
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

BLACK := $(shell command -v black 2> /dev/null)
BLACK_LINE_LENGTH ?= 100
BLACK_TARGET_VERSION ?= py310

# -----------------------------------------------------------------------------
# ОСНОВНЫЕ КОМАНДЫ
# -----------------------------------------------------------------------------

black-check: ## Проверить форматирование Python файлов
	@echo "🔍 Проверка форматирования..."
ifeq ($(BLACK),)
	@echo "❌ Black не установлен!"
	@exit 1
else
	@black --check $(PYTHON_FILES) || \
		(echo "❌ Требуется форматирование!"; exit 1)
	@echo "✅ Все файлы отформатированы правильно!"
endif

black-format: ## Отформатировать все Python файлы
	@echo "🎨 Форматирование файлов..."
ifeq ($(BLACK),)
	@echo "❌ Black не установлен!"
	@exit 1
else
	@black $(PYTHON_FILES)
	@echo "✅ Все файлы отформатированы!"
endif

black-quick: ## Быстрое форматирование (--fast)
	@echo "⚡ Быстрое форматирование..."
ifeq ($(BLACK),)
	@echo "❌ Black не установлен!"
	@exit 1
else
	@black --fast $(PYTHON_FILES)
	@echo "✅ Быстрое форматирование завершено!"
endif

black-strict: ## Строгое форматирование (без нормализации строк)
	@echo "📏 Строгое форматирование..."
ifeq ($(BLACK),)
	@echo "❌ Black не установлен!"
	@exit 1
else
	@black --skip-string-normalization $(PYTHON_FILES)
	@echo "✅ Строгое форматирование завершено!"
endif

black-safe: ## Безопасное форматирование (только если проверка пройдена)
	@echo "🛡️  Безопасное форматирование..."
	@if $(MAKE) -s black-check >/dev/null 2>&1; then \
		$(MAKE) black-format; \
	else \
		echo "❌ Безопасное форматирование отменено"; \
		exit 1; \
	fi

# -----------------------------------------------------------------------------
# ПРЕДПРОСМОТР И ДИАГНОСТИКА
# -----------------------------------------------------------------------------

black-diff: ## Показать различия (что изменится)
	@echo "🔬 Предпросмотр изменений..."
ifeq ($(BLACK),)
	@echo "❌ Black не установлен!"
	@exit 1
else
	@black --diff --color $(PYTHON_FILES) || true
endif

black-dry-run: ## Предпросмотр без применения (синоним для black-diff)
	@$(MAKE) black-diff

black-verbose: ## Подробный вывод процесса форматирования
	@echo "📊 Подробный вывод..."
ifeq ($(BLACK),)
	@echo "❌ Black не установлен!"
	@exit 1
else
	@black --verbose $(PYTHON_FILES)
endif

# -----------------------------------------------------------------------------
# РАБОТА С ФАЙЛАМИ И ПАПКАМИ
# -----------------------------------------------------------------------------

black-file: ## Отформатировать конкретный файл (FILE=path.py)
ifeq ($(BLACK),)
	@echo "❌ Black не установлен!"
	@exit 1
else ifeq ($(FILE),)
	@echo "❌ Укажите файл: make black-file FILE=path.py"
	@exit 1
else ifneq ($(wildcard $(FILE)),)
	@echo "📄 Форматирование файла: $(FILE)"
	@black $(FILE)
	@echo "✅ Файл отформатирован!"
else
	@echo "❌ Файл не найден: $(FILE)"
	@exit 1
endif

black-dir: ## Отформатировать папку (DIR=path/)
ifeq ($(BLACK),)
	@echo "❌ Black не установлен!"
	@exit 1
else ifeq ($(DIR),)
	@echo "❌ Укажите папку: make black-dir DIR=path/"
	@exit 1
else ifneq ($(wildcard $(DIR)),)
	@echo "📁 Форматирование папки: $(DIR)"
	@find $(DIR) -name "*.py" -exec black {} \;
	@echo "✅ Папка отформатирована!"
else
	@echo "❌ Папка не найдена: $(DIR)"
	@exit 1
endif

# -----------------------------------------------------------------------------
# КОНФИГУРАЦИЯ И ПРЕСЕТЫ
# -----------------------------------------------------------------------------

black-config: ## Показать текущую конфигурацию Black
	@echo "⚙️  Конфигурация Black:"
	@echo "  Длина строки: $(BLACK_LINE_LENGTH)"
	@echo "  Версия Python: $(BLACK_TARGET_VERSION)"

black-version: ## Показать версию Black
	@echo "ℹ️  Информация о Black:"
ifeq ($(BLACK),)
	@echo "❌ Black не установлен!"
else
	@black --version
	@echo ""
	@echo "Файлов для форматирования: $$(echo "$(PYTHON_FILES)" | wc -w | tr -d ' ')"
endif

black-line-79: ## Форматирование по PEP 8 (79 символов)
	@echo "📐 PEP 8 форматирование (79 символов)..."
	@BLACK_LINE_LENGTH=79 $(MAKE) black-format

black-line-120: ## Современное форматирование (120 символов)
	@echo "💎 Современное форматирование (120 символов)..."
	@BLACK_LINE_LENGTH=120 $(MAKE) black-format

# -----------------------------------------------------------------------------
# УСТАНОВКА И УТИЛИТЫ
# -----------------------------------------------------------------------------

install-black: ## Установить или обновить Black
	@echo "📦 Установка Black..."
	@pip install --upgrade black
	@echo "✅ Black установлен!"
	@black --version

# -----------------------------------------------------------------------------
# АЛИАСЫ
# -----------------------------------------------------------------------------

format: black-format ## Форматировать все файлы (алиас для black-format)
	@echo "✅ Форматирование завершено"

check: black-check ## Проверить форматирование (алиас для black-check)
	@echo "✅ Проверка завершена"

# -----------------------------------------------------------------------------
# PHONY ЦЕЛИ
# -----------------------------------------------------------------------------
.PHONY: black-check black-format black-quick black-strict black-safe \
        black-diff black-dry-run black-verbose black-file black-dir \
        black-config black-version black-line-79 black-line-120 \
        install-black format check
