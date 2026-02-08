# =============================================================================
## CATEGORY: isort - Python Import Sorting
# КОМАНДЫ ДЛЯ СОРТИРОВКИ ИМПОРТОВ PYTHON
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

ISORT := $(shell command -v isort 2> /dev/null)
ISORT_PROFILE ?= black
ISORT_LINE_LENGTH ?= 100

# -----------------------------------------------------------------------------
# ОСНОВНЫЕ КОМАНДЫ
# -----------------------------------------------------------------------------

isort-check: ## Проверить сортировку импортов
	@echo "🔍 Проверка сортировки импортов..."
ifeq ($(ISORT),)
	@echo "❌ isort не установлен!"
	@exit 1
else
	@isort --check-only --diff $(PYTHON_FILES) || \
		(echo "❌ Требуется сортировка импортов!"; exit 1)
	@echo "✅ Все импорты отсортированы правильно!"
endif

isort-sort: ## Отсортировать импорты во всех файлах
	@echo "📊 Сортировка импортов..."
ifeq ($(ISORT),)
	@echo "❌ isort не установлен!"
	@exit 1
else
	@isort $(PYTHON_FILES)
	@echo "✅ Все импорты отсортированы!"
endif

isort-diff: ## Показать различия (что изменится)
	@echo "🔬 Предпросмотр изменений импортов..."
ifeq ($(ISORT),)
	@echo "❌ isort не установлен!"
	@exit 1
else
	@isort --diff $(PYTHON_FILES) || true
endif

isort-dry-run: ## Предпросмотр без применения
	@$(MAKE) isort-diff

# -----------------------------------------------------------------------------
# РАБОТА С ФАЙЛАМИ И ПАПКАМИ
# -----------------------------------------------------------------------------

isort-file: ## Отсортировать импорты в конкретном файле (FILE=path.py)
ifeq ($(ISORT),)
	@echo "❌ isort не установлен!"
	@exit 1
else ifeq ($(FILE),)
	@echo "❌ Укажите файл: make isort-file FILE=path.py"
	@exit 1
else ifneq ($(wildcard $(FILE)),)
	@echo "📄 Сортировка импортов в файле: $(FILE)"
	@isort $(FILE)
	@echo "✅ Импорты отсортированы!"
else
	@echo "❌ Файл не найден: $(FILE)"
	@exit 1
endif

isort-dir: ## Отсортировать импорты в папке (DIR=path/)
ifeq ($(ISORT),)
	@echo "❌ isort не установлен!"
	@exit 1
else ifeq ($(DIR),)
	@echo "❌ Укажите папку: make isort-dir DIR=path/"
	@exit 1
else ifneq ($(wildcard $(DIR)),)
	@echo "📁 Сортировка импортов в папке: $(DIR)"
	@find $(DIR) -name "*.py" -exec isort {} \;
	@echo "✅ Импорты в папке отсортированы!"
else
	@echo "❌ Папка не найдена: $(DIR)"
	@exit 1
endif

# -----------------------------------------------------------------------------
# КОНФИГУРАЦИЯ И ПРОФИЛИ
# -----------------------------------------------------------------------------

isort-config: ## Показать текущую конфигурацию isort
	@echo "⚙️  Конфигурация isort:"
	@echo "  Профиль: $(ISORT_PROFILE)"
	@echo "  Длина строки: $(ISORT_LINE_LENGTH)"
	@echo "  Файлов для обработки: $$(echo "$(PYTHON_FILES)" | wc -w | tr -d ' ')"

isort-version: ## Показать версию isort
	@echo "ℹ️  Информация о isort:"
ifeq ($(ISORT),)
	@echo "❌ isort не установлен!"
else
	@isort --version
endif

# -----------------------------------------------------------------------------
# ПРОФИЛИ И РЕЖИМЫ
# -----------------------------------------------------------------------------

isort-profile-black: ## Использовать профиль совместимый с Black
	@echo "🎨 Установка профиля Black..."
	@ISORT_PROFILE=black $(MAKE) isort-sort

isort-profile-django: ## Использовать профиль Django
	@echo "⚡ Установка профиля Django..."
	@ISORT_PROFILE=django $(MAKE) isort-sort

isort-atomic: ## Атомарная сортировка (проверка перед записью)
	@echo "🛡️  Атомарная сортировка..."
ifeq ($(ISORT),)
	@echo "❌ isort не установлен!"
	@exit 1
else
	@isort --atomic $(PYTHON_FILES)
	@echo "✅ Атомарная сортировка завершена!"
endif

# -----------------------------------------------------------------------------
# УСТАНОВКА
# -----------------------------------------------------------------------------

install-isort: ## Установить или обновить isort
	@echo "📦 Установка isort..."
	@pip install --upgrade isort
	@echo "✅ isort установлен!"
	@isort --version

# -----------------------------------------------------------------------------
# КОМБИНИРОВАННЫЕ КОМАНДЫ
# -----------------------------------------------------------------------------

isort-then-black: ## Сначала отсортировать импорты, потом отформатировать
	@echo "🔄 isort -> black..."
	@$(MAKE) isort-sort
	@$(MAKE) black-format
	@echo "✅ Комбинированная обработка завершена!"

black-then-isort: ## Сначала отформатировать, потом отсортировать импорты
	@echo "🔄 black -> isort..."
	@$(MAKE) black-format
	@$(MAKE) isort-sort
	@echo "✅ Комбинированная обработка завершена!"

# -----------------------------------------------------------------------------
# PHONY ЦЕЛИ
# -----------------------------------------------------------------------------
.PHONY: isort-check isort-sort isort-diff isort-dry-run \
	isort-file isort-dir isort-config isort-version \
	isort-profile-black isort-profile-django isort-atomic \
	install-isort isort-then-black black-then-isort
