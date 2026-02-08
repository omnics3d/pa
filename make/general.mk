# =============================================================================
## CATEGORY: General - General Utilities
# ОБЩИЕ УТИЛИТЫ - ТОЛЬКО 2 КОМАНДЫ
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

python-files: ## Показать все Python файлы
	@echo "🐍 Python файлы:"
	@for file in $(PYTHON_FILES); do \
		echo "  $$file"; \
	done
	@echo ""
	@echo "Всего: $$(echo "$(PYTHON_FILES)" | wc -w | tr -d ' ') файлов"

clean: ## Очистить временные файлы
	@echo "🧹 Очистка временных файлов..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name ".DS_Store" -delete
	rm -rf build/ dist/ *.egg-info/
	@echo "✅ Очистка завершена!"
