# =============================================================================
## CATEGORY: Mypy - Python Static Type Checker
# КОМАНДЫ ДЛЯ ПРОВЕРКИ ТИПОВ PYTHON КОДА
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

MYPY := $(shell command -v mypy 2> /dev/null)
MYPY_CONFIG ?= .mypy.ini
MYPY_STRICT ?= false

# -----------------------------------------------------------------------------
# ОСНОВНЫЕ КОМАНДЫ
# -----------------------------------------------------------------------------

mypy-check: ## Проверить типы во всех файлах
	@echo "🔍 Проверка типов Mypy..."
ifeq ($(MYPY),)
	@echo "❌ Mypy не установлен!"
	@exit 1
else
	@mypy $(PYTHON_FILES) || true
	@echo "✅ Проверка типов завершена!"
endif

mypy-strict: ## Строгая проверка типов
	@echo "📏 Строгая проверка типов..."
ifeq ($(MYPY),)
	@echo "❌ Mypy не установлен!"
	@exit 1
else
	@mypy --strict $(PYTHON_FILES) || true
endif

mypy-no-error-summary: ## Проверка без сводки ошибок
	@echo "📊 Проверка без сводки..."
ifeq ($(MYPY),)
	@echo "❌ Mypy не установлен!"
	@exit 1
else
	@mypy --no-error-summary $(PYTHON_FILES) || true
endif

mypy-verbose: ## Подробный вывод
	@echo "📋 Подробная проверка типов..."
ifeq ($(MYPY),)
	@echo "❌ Mypy не установлен!"
	@exit 1
else
	@mypy --verbose $(PYTHON_FILES) || true
endif

# -----------------------------------------------------------------------------
# РАБОТА С ФАЙЛАМИ И ПАПКАМИ
# -----------------------------------------------------------------------------

mypy-file: ## Проверить конкретный файл (FILE=path.py)
ifeq ($(MYPY),)
	@echo "❌ Mypy не установлен!"
	@exit 1
else ifeq ($(FILE),)
	@echo "❌ Укажите файл: make mypy-file FILE=path.py"
	@exit 1
else ifneq ($(wildcard $(FILE)),)
	@echo "📄 Проверка типов в файле: $(FILE)"
	@mypy $(FILE)
else
	@echo "❌ Файл не найден: $(FILE)"
	@exit 1
endif

mypy-dir: ## Проверить папку (DIR=path/)
ifeq ($(MYPY),)
	@echo "❌ Mypy не установлен!"
	@exit 1
else ifeq ($(DIR),)
	@echo "❌ Укажите папку: make mypy-dir DIR=path/"
	@exit 1
else ifneq ($(wildcard $(DIR)),)
	@echo "📁 Проверка типов в папке: $(DIR)"
	@mypy $(DIR) || true
	@echo "✅ Проверка папки завершена!"
else
	@echo "❌ Папка не найдена: $(DIR)"
	@exit 1
endif

# -----------------------------------------------------------------------------
# КОНФИГУРАЦИЯ
# -----------------------------------------------------------------------------

mypy-config: ## Показать конфигурацию
	@echo "⚙️  Конфигурация Mypy:"
	@echo "  Конфиг файл: $(MYPY_CONFIG)"
	@echo "  Строгий режим: $(MYPY_STRICT)"
	@echo "  Файлов для проверки: $$(echo "$(PYTHON_FILES)" | wc -w | tr -d ' ')"

mypy-version: ## Показать версию
	@echo "ℹ️  Информация о Mypy:"
ifeq ($(MYPY),)
	@echo "❌ Mypy не установлен!"
else
	@mypy --version
endif

mypy-show-config: ## Показать фактическую конфигурацию
	@echo "🔧 Фактическая конфигурация Mypy:"
ifeq ($(MYPY),)
	@echo "❌ Mypy не установлен!"
	@exit 1
else
	@mypy --show-config $(PYTHON_FILES) 2>/dev/null || true
endif

# -----------------------------------------------------------------------------
# РЕЖИМЫ ПРОВЕРКИ
# -----------------------------------------------------------------------------

mypy-incremental: ## Инкрементальная проверка (быстрее)
	@echo "⚡ Инкрементальная проверка..."
ifeq ($(MYPY),)
	@echo "❌ Mypy не установлен!"
	@exit 1
else
	@mypy --incremental $(PYTHON_FILES) || true
endif

mypy-no-incremental: ## Полная проверка (без кэша)
	@echo "🔄 Полная проверка (без кэша)..."
ifeq ($(MYPY),)
	@echo "❌ Mypy не установлен!"
	@exit 1
else
	@mypy --no-incremental $(PYTHON_FILES) || true
endif

mypy-warn-unused: ## Предупреждения о неиспользуемых
	@echo "⚠️  Проверка с предупреждениями о неиспользуемых..."
ifeq ($(MYPY),)
	@echo "❌ Mypy не установлен!"
	@exit 1
else
	@mypy --warn-unused-ignores --warn-unused-configs $(PYTHON_FILES) || true
endif

# -----------------------------------------------------------------------------
# ФИЛЬТРЫ И ИСКЛЮЧЕНИЯ
# -----------------------------------------------------------------------------

mypy-ignore-errors: ## Проверка с игнорированием ошибок (список через запятую)
ifeq ($(MYPY),)
	@echo "❌ Mypy не установлен!"
	@exit 1
else ifeq ($(ERROR_CODES),)
	@echo "❌ Укажите коды ошибок: make mypy-ignore-errors ERROR_CODES=error1,error2"
	@exit 1
else
	@echo "🙈 Игнорирование ошибок: $(ERROR_CODES)"
	@mypy --disable-error-code=$(ERROR_CODES) $(PYTHON_FILES) || true
endif

mypy-only-errors: ## Только конкретные типы ошибок (список через запятую)
ifeq ($(MYPY),)
	@echo "❌ Mypy не установлен!"
	@exit 1
else ifeq ($(ERROR_CODES),)
	@echo "❌ Укажите коды ошибок: make mypy-only-errors ERROR_CODES=error1,error2"
	@exit 1
else
	@echo "🎯 Только ошибки: $(ERROR_CODES)"
	@mypy --enable-error-code=$(ERROR_CODES) $(PYTHON_FILES) || true
endif

# -----------------------------------------------------------------------------
# УСТАНОВКА
# -----------------------------------------------------------------------------

install-mypy: ## Установить или обновить Mypy
	@echo "📦 Установка Mypy..."
	@pip install --upgrade mypy
	@echo "✅ Mypy установлен!"
	@mypy --version

# -----------------------------------------------------------------------------
# PHONY ЦЕЛИ
# -----------------------------------------------------------------------------
.PHONY: mypy-check mypy-strict mypy-no-error-summary mypy-verbose \
	mypy-file mypy-dir mypy-config mypy-version mypy-show-config \
	mypy-incremental mypy-no-incremental mypy-warn-unused \
	mypy-ignore-errors mypy-only-errors \
	install-mypy
