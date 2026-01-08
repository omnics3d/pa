import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# --- 1. Pydantic Модели ---

class LoadDate(BaseModel):
    """Модель дат загрузки данных."""
    start_load: str
    end_load: str


class Tool(BaseModel):
    """Модель торгового инструмента."""
    name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    load_date: LoadDate


class MarketParameters(BaseModel):
    """Параметры типа рынка (spot, linear и т.д.)."""
    full_name: str
    short_name: str
    rus_name: str


class Market(BaseModel):
    """Модель рынка, содержащая список инструментов."""
    parameters: MarketParameters
    tools: List[Tool]


class ExchangeParameters(BaseModel):
    """Общие параметры биржи."""
    full_name: str
    short_name: str
    rus_name: str
    path_load: str


class Exchange(BaseModel):
    """Модель биржи, содержащая список рынков."""
    parameters: ExchangeParameters
    markets: List[Market]


class ExchangesData(BaseModel):
    """Корневая модель данных всего XML-файла."""
    exchange: List[Exchange]


# --- 2. Основной класс управления данными ---

class ExchangeDataManager:
    """Класс для управления данными бирж через XML и Pydantic.

    Позволяет валидировать, искать и изменять данные в XML-файле.
    Актуально для 2026 года.
    """

    file_path: str
    tree: ET.ElementTree
    root: ET.Element
    model: ExchangesData

    def __init__(self, xml_file_path: str) -> None:
        """Инициализирует менеджер и выполняет первичный парсинг."""
        self.file_path = xml_file_path
        self.tree = ET.parse(xml_file_path)
        self.root = self.tree.getroot()
        self._refresh_model()

    def _refresh_model(self) -> None:
        """Синхронизирует Pydantic модель с текущим XML деревом."""
        data_dict = self._xml_to_dict(self.root)
        self.model = ExchangesData.model_validate(data_dict)

    def _xml_to_dict(self, root_elem: ET.Element) -> Dict[str, Any]:
        """Преобразует XML структуру в словарь для Pydantic."""
        ex_list = []
        for ex_el in root_elem.findall('exchange'):
            params = ex_el.find('parameters')
            if params is None:
                continue

            ex_dict = {
                'parameters': {c.tag: c.text for c in params},
                'markets': []
            }

            markets_node = ex_el.find('markets')
            if markets_node is not None:
                for mk_el in markets_node.findall('market'):
                    mk_params = mk_el.find('parameters')
                    if mk_params is None:
                        continue

                    mk_dict = {
                        'parameters': {
                            c.tag: (c.text if c.text else "")
                            for c in mk_params
                        },
                        'tools': []
                    }

                    tools_node = mk_el.find('tools')
                    if tools_node is not None:
                        for tl_el in tools_node.findall('tool'):
                            name_el = tl_el.find('name')
                            ld_el = tl_el.find('load_date')
                            if name_el is not None and ld_el is not None:
                                mk_dict['tools'].append({
                                    'name': name_el.text,
                                    'parameters': {},
                                    'load_date': {
                                        c.tag: c.text for c in ld_el
                                    }
                                })
                    ex_dict['markets'].append(mk_dict)
            ex_list.append(ex_dict)
        return {'exchange': ex_list}

    # --- Методы проверки ---

    def is_exchange_exists(self, exchange_name: str) -> bool:
        """Проверяет существование биржи (case-insensitive)."""
        return any(
            ex.parameters.full_name.lower() == exchange_name.lower()
            for ex in self.model.exchange
        )

    def is_market_exists(self, exchange_name: str, market_name: str) -> bool:
        """Проверяет наличие рынка в конкретной бирже."""
        for ex in self.model.exchange:
            if ex.parameters.full_name.lower() == exchange_name.lower():
                return any(
                    m.parameters.full_name.lower() == market_name.lower()
                    for m in ex.markets
                )
        return False

    def is_tool_exists(self, exchange_name: str,
                       market_name: str, tool_name: str) -> bool:
        """Проверяет наличие инструмента в заданном рынке и бирже."""
        return self._find_tool_model(
            exchange_name, market_name, tool_name
        ) is not None

    # --- Методы получения данных ---

    def get_exchange_names(self) -> List[str]:
        """Возвращает список имен всех бирж из файла."""
        return [ex.parameters.full_name for ex in self.model.exchange]

    def get_path_load_for_exchange(self, exchange_name: str) -> Optional[str]:
        """Возвращает путь загрузки (URL) для биржи."""
        for ex in self.model.exchange:
            if ex.parameters.full_name.lower() == exchange_name.lower():
                return ex.parameters.path_load
        return None

    def get_markets_for_exchange(self,
                                 exchange_name: str) -> Optional[List[str]]:
        """Возвращает список доступных рынков для биржи."""
        for ex in self.model.exchange:
            if ex.parameters.full_name.lower() == exchange_name.lower():
                return [m.parameters.full_name for m in ex.markets]
        return None

    def get_tools_for_market(self, exchange_name: str,
                             market_name: str) -> Optional[List[str]]:
        """Возвращает список инструментов для рынка."""
        for ex in self.model.exchange:
            if ex.parameters.full_name.lower() == exchange_name.lower():
                for m in ex.markets:
                    if m.parameters.full_name.lower() == market_name.lower():
                        return [t.name for t in m.tools]
        return None

    def get_start_date_for_tool(self, exchange_name: str,
                                market_name: str,
                                tool_name: str) -> Optional[str]:
        """Возвращает дату начала загрузки инструмента."""
        tool = self._find_tool_model(exchange_name, market_name, tool_name)
        return tool.load_date.start_load if tool else None

    def get_end_date_for_tool(self, exchange_name: str,
                              market_name: str,
                              tool_name: str) -> Optional[str]:
        """Возвращает дату конца загрузки инструмента."""
        tool = self._find_tool_model(exchange_name, market_name, tool_name)
        return tool.load_date.end_load if tool else None

    def _find_tool_model(self, exchange_name: str,
                         market_name: str,
                         tool_name: str) -> Optional[Tool]:
        """Внутренний поиск инструмента в Pydantic модели."""
        for ex in self.model.exchange:
            if ex.parameters.full_name.lower() == exchange_name.lower():
                for m in ex.markets:
                    if m.parameters.full_name.lower() == market_name.lower():
                        for t in m.tools:
                            if t.name.upper() == tool_name.upper():
                                return t
        return None

    # --- Методы модификации и сохранения ---

    def update_end_load_date(self, exchange_name: str, market_name: str,
                             tool_name: str, new_date: str) -> bool:
        """Обновляет дату конца загрузки в XML. Возвращает True при успехе."""
        updated = False
        for exch in self.root.findall('exchange'):
            ex_name_el = exch.find('parameters/full_name')
            if (ex_name_el is not None and
                    ex_name_el.text.lower() == exchange_name.lower()):
                for mkt in exch.findall('markets/market'):
                    mk_name_el = mkt.find('parameters/full_name')
                    if (mk_name_el is not None and
                            mk_name_el.text.lower() == market_name.lower()):
                        for tool in mkt.findall('tools/tool'):
                            tl_name_el = tool.find('name')
                            if (tl_name_el is not None and
                                    tl_name_el.text.upper() ==
                                    tool_name.upper()):
                                end_ld_el = tool.find('load_date/end_load')
                                if end_ld_el is not None:
                                    end_ld_el.text = new_date
                                    updated = True
        if updated:
            self._refresh_model()
        return updated

    def save_changes(self, output_path: Optional[str] = None) -> None:
        """Сохраняет текущие изменения в XML файл."""
        path = output_path if output_path else self.file_path
        self.tree.write(path, encoding='utf-8', xml_declaration=True)

    def get_full_xml_string(self) -> str:
        """Возвращает текущий XML в виде форматированной строки."""
        return ET.tostring(self.root, encoding='unicode')

