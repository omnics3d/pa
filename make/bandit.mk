# =============================================================================
## CATEGORY: Bandit - Security Linter
# КОМАНДЫ ДЛЯ ПРОВЕРКИ БЕЗОПАСНОСТИ PYTHON КОДА
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

BANDIT := $(shell command -v bandit 2> /dev/null)
BANDIT_CONFIG ?= .bandit.yml
BANDIT_SEVERITY ?= MEDIUM,HIGH
BANDIT_CONFIDENCE ?= MEDIUM,HIGH

# -----------------------------------------------------------------------------
# ОСНОВНЫЕ КОМАНДЫ
# -----------------------------------------------------------------------------

bandit-check: ## Проверить безопасность всех файлов
	@echo "🔒 Проверка безопасности Bandit..."
ifeq ($(BANDIT),)
	@echo "❌ Bandit не установлен!"
	@exit 1
else
	@bandit -r . -f custom --msg-template '{path}:{line}: {test_id}: {severity}: {msg}' || true
	@echo "✅ Проверка безопасности завершена!"
endif

bandit-quick: ## Быстрая проверка безопасности
	@echo "⚡ Быстрая проверка безопасности..."
ifeq ($(BANDIT),)
	@echo "❌ Bandit не установлен!"
	@exit 1
else
	@bandit -r . -f custom --msg-template '{path}:{line}: {test_id}: {severity}: {msg}' -s $(BANDIT_SEVERITY) -c $(BANDIT_CONFIDENCE) || true
endif

bandit-format-json: ## Проверка с выводом в JSON
	@echo "📄 Проверка с JSON выводом..."
ifeq ($(BANDIT),)
	@echo "❌ Bandit не установлен!"
	@exit 1
else
	@bandit -r . -f json || true
endif

bandit-format-txt: ## Проверка с текстовым выводом
	@echo "📝 Проверка с текстовым выводом..."
ifeq ($(BANDIT),)
	@echo "❌ Bandit не установлен!"
	@exit 1
else
	@bandit -r . -f txt || true
endif

# -----------------------------------------------------------------------------
# РАБОТА С ФАЙЛАМИ И ПАПКАМИ
# -----------------------------------------------------------------------------

bandit-file: ## Проверить конкретный файл (FILE=path.py)
ifeq ($(BANDIT),)
	@echo "❌ Bandit не установлен!"
	@exit 1
else ifeq ($(FILE),)
	@echo "❌ Укажите файл: make bandit-file FILE=path.py"
	@exit 1
else ifneq ($(wildcard $(FILE)),)
	@echo "📄 Проверка безопасности файла: $(FILE)"
	@bandit -f custom --msg-template '{path}:{line}: {test_id}: {severity}: {msg}' $(FILE)
else
	@echo "❌ Файл не найден: $(FILE)"
	@exit 1
endif

bandit-dir: ## Проверить папку (DIR=path/)
ifeq ($(BANDIT),)
	@echo "❌ Bandit не установлен!"
	@exit 1
else ifeq ($(DIR),)
	@echo "❌ Укажите папку: make bandit-dir DIR=path/"
	@exit 1
else ifneq ($(wildcard $(DIR)),)
	@echo "📁 Проверка безопасности папки: $(DIR)"
	@bandit -r $(DIR) -f custom --msg-template '{path}:{line}: {test_id}: {severity}: {msg}' || true
	@echo "✅ Проверка папки завершена!"
else
	@echo "❌ Папка не найдена: $(DIR)"
	@exit 1
endif

# -----------------------------------------------------------------------------
# КОНФИГУРАЦИЯ И ФИЛЬТРЫ
# -----------------------------------------------------------------------------

bandit-config: ## Показать конфигурацию
	@echo "⚙️  Конфигурация Bandit:"
	@echo "  Конфиг файл: $(BANDIT_CONFIG)"
	@echo "  Уровень опасности: $(BANDIT_SEVERITY)"
	@echo "  Уровень уверенности: $(BANDIT_CONFIDENCE)"
	@echo "  Файлов для проверки: $$(echo "$(PYTHON_FILES)" | wc -w | tr -d ' ')"

bandit-version: ## Показать версию
	@echo "ℹ️  Информация о Bandit:"
ifeq ($(BANDIT),)
	@echo "❌ Bandit не установлен!"
else
	@bandit --version
endif

bandit-skip: ## Пропустить конкретные тесты (через запятую)
ifeq ($(BANDIT),)
	@echo "❌ Bandit не установлен!"
	@exit 1
else ifeq ($(TESTS),)
	@echo "❌ Укажите тесты: make bandit-skip TESTS=B101,B102"
	@exit 1
else
	@echo "⏭️  Пропуск тестов: $(TESTS)"
	@bandit -r . -f custom --msg-template '{path}:{line}: {test_id}: {severity}: {msg}' -s $(BANDIT_SEVERITY) -c $(BANDIT_CONFIDENCE) --skip $(TESTS) || true
endif

# -----------------------------------------------------------------------------
# УРОВНИ ПРОВЕРКИ
# -----------------------------------------------------------------------------

bandit-high-only: ## Только критические уязвимости (HIGH)
	@echo "🚨 Только критические уязвимости..."
	@BANDIT_SEVERITY=HIGH $(MAKE) bandit-quick

bandit-medium-high: ## Средние и критические уязвимости (MEDIUM,HIGH)
	@echo "⚠️  Средние и критические уязвимости..."
	@BANDIT_SEVERITY=MEDIUM,HIGH $(MAKE) bandit-quick

bandit-all-levels: ## Все уровни уязвимостей (LOW,MEDIUM,HIGH)
	@echo "🔍 Все уровни уязвимостей..."
	@BANDIT_SEVERITY=LOW,MEDIUM,HIGH $(MAKE) bandit-quick

# -----------------------------------------------------------------------------
# СПЕЦИАЛЬНЫЕ ПРОВЕРКИ
# -----------------------------------------------------------------------------

bandit-aggressive: ## Агрессивная проверка (больше тестов)
	@echo "🔥 Агрессивная проверка..."
ifeq ($(BANDIT),)
	@echo "❌ Bandit не установлен!"
	@exit 1
else
	@bandit -r . -f custom --msg-template '{path}:{line}: {test_id}: {severity}: {msg}' -lll || true
endif

bandit-baseline: ## Сравнение с базовым отчетом (BASELINE=report.json)
ifeq ($(BANDIT),)
	@echo "❌ Bandit не установлен!"
	@exit 1
else ifeq ($(BASELINE),)
	@echo "❌ Укажите базовый отчет: make bandit-baseline BASELINE=report.json"
	@exit 1
else ifneq ($(wildcard $(BASELINE)),)
	@echo "📊 Сравнение с базовым отчетом: $(BASELINE)"
	@bandit -r . -f custom --msg-template '{path}:{line}: {test_id}: {severity}: {msg}' --baseline $(BASELINE) || true
else
	@echo "❌ Базовый отчет не найден: $(BASELINE)"
	@exit 1
endif

# -----------------------------------------------------------------------------
# УСТАНОВКА
# -----------------------------------------------------------------------------

install-bandit: ## Установить или обновить Bandit
	@echo "📦 Установка Bandit..."
	@pip install --upgrade bandit
	@echo "✅ Bandit установлен!"
	@bandit --version

# -----------------------------------------------------------------------------
# ГЕНЕРАЦИЯ ОТЧЕТОВ
# -----------------------------------------------------------------------------

bandit-report-html: ## Генерация HTML отчета (OUTPUT=report.html)
ifeq ($(BANDIT),)
	@echo "❌ Bandit не установлен!"
	@exit 1
else
	@echo "📊 Генерация HTML отчета..."
	@bandit -r . -f html -o $(or $(OUTPUT), bandit_report.html) || true
	@echo "✅ HTML отчет создан: $(or $(OUTPUT), bandit_report.html)"
endif

bandit-report-json: ## Генерация JSON отчета (OUTPUT=report.json)
ifeq ($(BANDIT),)
	@echo "❌ Bandit не установлен!"
	@exit 1
else
	@echo "📊 Генерация JSON отчета..."
	@bandit -r . -f json -o $(or $(OUTPUT), bandit_report.json) || true
	@echo "✅ JSON отчет создан: $(or $(OUTPUT), bandit_report.json)"
endif

# -----------------------------------------------------------------------------
# PHONY ЦЕЛИ
# -----------------------------------------------------------------------------
.PHONY: bandit-check bandit-quick bandit-format-json bandit-format-txt \
	bandit-file bandit-dir bandit-config bandit-version bandit-skip \
	bandit-high-only bandit-medium-high bandit-all-levels \
	bandit-aggressive bandit-baseline \
	install-bandit bandit-report-html bandit-report-json
