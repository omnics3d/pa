# =============================================================================
## CATEGORY: Project - Project Management
# УПРАВЛЕНИЕ ПРОЕКТОМ
# =============================================================================

PROJECT_NAME := $(shell grep -E '^name\s*=' pyproject.toml | head -1 | sed -E 's/^name\s*=\s*"([^"]+)"\s*/\1/')
PROJECT_VERSION := $(shell grep -E '^version\s*=' pyproject.toml | head -1 | sed -E 's/^version\s*=\s*"([^"]+)"\s*/\1/')
PYTHON_REQUIRES := $(shell grep -E '^requires-python\s*=' pyproject.toml | head -1 | sed -E 's/^requires-python\s*=\s*"([^"]+)"\s*/\1/')
PROJECT_DESCRIPTION := $(shell grep -E '^description\s*=' pyproject.toml | head -1 | sed -E 's/^description\s*=\s*"([^"]+)"\s*/\1/')

info: ## Показать информацию о проекте
	@echo "📊 Информация о проекте:"
	@echo "  Название:    $(PROJECT_NAME)"
	@echo "  Версия:      $(PROJECT_VERSION)"
	@echo "  Описание:    $(PROJECT_DESCRIPTION)"
	@echo "  Python:      $(PYTHON_REQUIRES)"

install: ## Установить проект в систему
	@echo "📦 Установка проекта..."
	pip install .
	@echo "✅ Проект установлен!"

dev: ## Установить в режиме разработки
	@echo "🔧 Режим разработки..."
	pip install -e .
	@echo "✅ Проект установлен в режиме разработки!"

debug-vars: ## Показать значения переменных (отладка)
	@echo "PROJECT_NAME: '$(PROJECT_NAME)'"
	@echo "PROJECT_VERSION: '$(PROJECT_VERSION)'"
	@echo "PYTHON_REQUIRES: '$(PYTHON_REQUIRES)'"
	@echo "PROJECT_DESCRIPTION: '$(PROJECT_DESCRIPTION)'"

test_import: ## Протестировать импорты модулей
	@echo "🧪 Тест импортов..."
	@for module in core utils tasks; do \
		echo "Проверка $$module..."; \
		python3 -c "import $$module" && echo "  ✓ OK" || echo "  ✗ Ошибка"; \
	done
