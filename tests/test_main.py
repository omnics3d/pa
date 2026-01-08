import pytest
from unittest.mock import MagicMock, patch
import importlib

import main

@pytest.fixture
def mock_logger():
    with patch('main.logger') as mock:
        yield mock

def test_run_selected_script_success(mock_logger):
    # 1. Создаем мок для модуля, который будет загружаться
    mock_module = MagicMock()
    # Важно: hasattr(mock_module, "run") должен вернуть True
    # MagicMock по умолчанию создает любые атрибуты при обращении,
    # но для надежности можно явно задать метод:
    mock_module.run = MagicMock()

    # 2. Патчим ТАМ, ГДЕ эти функции используются (в файле main.py)
    with patch('main.importlib.import_module') as mock_import, \
            patch('main.importlib.reload') as mock_reload:
                                                                 
        # Настраиваем, чтобы и импорт, и релоад возвращали ОДИН И ТОТ ЖЕ объект
        mock_import.return_value = mock_module
        mock_reload.return_value = mock_module
        
        # 3. Запуск
        main.run_selected_script("some_script")
        
        # 4. Теперь проверка сработает
        mock_module.run.assert_called_once()
