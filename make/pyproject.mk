# =============================================================================
# MAKEFILE ДЛЯ ЧТЕНИЯ pyproject.toml (v2026)
# Этот файл содержит все переменные и правила для работы с pyproject.toml
# =============================================================================

# -----------------------------------------------------------------------------
# ОПРЕДЕЛЕНИЕ ПЕРЕМЕННЫХ ИЗ pyproject.toml
# -----------------------------------------------------------------------------

# Чтение имени проекта
PROJECT_NAME := $(shell grep -E '^name\s*=' pyproject.toml | head -1 | sed -E 's/^name\s*=\s*"([^"]+)"\s*/\1/')

# Чтение версии проекта
PROJECT_VERSION := $(shell grep -E '^version\s*=' pyproject.toml | head -1 | sed -E 's/^version\s*=\s*"([^"]+)"\s*/\1/')

# Чтение требований к Python
PYTHON_REQUIRES := $(shell grep -E '^requires-python\s*=' pyproject.toml | head -1 | sed -E 's/^requires-python\s*=\s*"([^"]+)"\s*/\1/')

# Чтение описания проекта
PROJECT_DESCRIPTION := $(shell grep -E '^description\s*=' pyproject.toml | head -1 | sed -E 's/^description\s*=\s*"([^"]+)"\s*/\1/')

# Чтение зависимостей (простой и надежный sed вариант)
DEPENDENCIES := $(shell sed -n '/^dependencies = \[/,/^\]/p' pyproject.toml | grep '"' | sed 's/^[[:space:]]*"\([^"]*\)".*/\1/' | tr '\n' ' ')

# Чтение скриптов
ENTRY_POINT := $(shell grep -E '^pa\s*=' pyproject.toml | head -1 | sed -E 's/^pa\s*=\s*"([^"]+)"\s*/\1/')

# -----------------------------------------------------------------------------
# КОМАНДЫ ПРОЕКТА
# -----------------------------------------------------------------------------

.PHONY: info install dev clean test_import debug-vars

info: ## Показать информацию о проекте из pyproject.toml
	@echo "================================================================"
	@echo "ИНФОРМАЦИЯ О ПРОЕКТЕ"
	@echo "================================================================"
	@echo "Имя проекта:      $(PROJECT_NAME)"
	@echo "Версия:           $(PROJECT_VERSION)"
	@echo "Описание:         $(PROJECT_DESCRIPTION)"
	@echo "Требуется Python: $(PYTHON_REQUIRES)"
	@echo "Точка входа:      $(ENTRY_POINT)"
	@echo "Зависимости:"
	@sed -n '/^dependencies = \[/,/^\]/p' pyproject.toml | grep '"' | sed 's/^[[:space:]]*"\([^"]*\)".*/  • \1/'
	@echo "================================================================"

install: ## Установить проект в систему
	@echo "Установка проекта $(PROJECT_NAME) версии $(PROJECT_VERSION)..."
	pip install .

dev: ## Установить в режиме разработки
	@echo "Установка в режиме разработки..."
	pip install -e .

clean: ## Очистить временные файлы
	@echo "Очистка временных файлов..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name ".DS_Store" -delete
	rm -rf build/ dist/ *.egg-info/

test_import: ## Протестировать импорты модулей
	@echo "Тестирование импортов модулей..."
	@for module in core utils tasks; do \
		echo "Проверка модуля $$module..."; \
		python3 -c "import $$module" && echo "  ✓ OK" || echo "  ✗ Ошибка"; \
	done
	@echo "Тестирование точки входа..."
	@python3 -c "import main; print('  ✓ main.py импортирован')" || echo "  ✗ Ошибка импорта main.py"

debug-vars: ## Показать значения переменных (отладка)
	@echo "PROJECT_NAME:      '$(PROJECT_NAME)'"
	@echo "PROJECT_VERSION:   '$(PROJECT_VERSION)'"
	@echo "PYTHON_REQUIRES:   '$(PYTHON_REQUIRES)'"
	@echo "PROJECT_DESCRIPTION: '$(PROJECT_DESCRIPTION)'"
	@echo "DEPENDENCIES:      '$(DEPENDENCIES)'"
	@echo "ENTRY_POINT:       '$(ENTRY_POINT)'"
