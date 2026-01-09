import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class LoadDate:
    """Структура дат начала и завершения загрузки."""
    start_load: str
    end_load: str


@dataclass
class Tool:
    """Торговый инструмент и его параметры."""
    name: str
    load_date: LoadDate
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketParameters:
    """Описательные параметры рынка."""
    full_name: str
    short_name: str
    rus_name: str


@dataclass
class Market:
    """Рынок, содержащий список инструментов."""
    parameters: MarketParameters
    tools: List[Tool] = field(default_factory=list)


@dataclass
class ExchangeParameters:
    """Общие параметры биржи и путь загрузки."""
    full_name: str
    short_name: str
    rus_name: str
    path_load: str


@dataclass
class Exchange:
    """Биржа, содержащая список рынков."""
    parameters: ExchangeParameters
    markets: List[Market] = field(default_factory=list)


class ExchangeDataManager:
    """Менеджер для управления конфигурациями бирж через XML."""

    def __init__(self, xml_file_path: str) -> None:
        """Инициализация менеджера и загрузка данных из XML."""
        self.file_path = xml_file_path
        self.tree = ET.parse(xml_file_path)
        self.root = self.tree.getroot()
        self.exchanges: List[Exchange] = []
        self._refresh_model()

    def _refresh_model(self) -> None:
        """Синхронизация внутренних объектов с XML-деревом."""
        self.exchanges = []
        for ex_el in self.root.findall('exchange'):
            p = ex_el.find('parameters')
            if p is None:
                continue

            ex_params = ExchangeParameters(
                full_name=p.findtext('full_name', ''),
                short_name=p.findtext('short_name', ''),
                rus_name=p.findtext('rus_name', ''),
                path_load=p.findtext('path_load', '')
            )
            exchange = Exchange(parameters=ex_params)

            m_node = ex_el.find('markets')
            if m_node is not None:
                for mk_el in m_node.findall('market'):
                    mp = mk_el.find('parameters')
                    if mp is None:
                        continue

                    m_params = MarketParameters(
                        full_name=mp.findtext('full_name', ''),
                        short_name=mp.findtext('short_name', ''),
                        rus_name=mp.findtext('rus_name', '')
                    )
                    market = Market(parameters=m_params)

                    t_node = mk_el.find('tools')
                    if t_node is not None:
                        for tl_el in t_node.findall('tool'):
                            ld = tl_el.find('load_date')
                            if ld is not None:
                                tool = Tool(
                                    name=tl_el.findtext('name', ''),
                                    load_date=LoadDate(
                                        start_load=ld.findtext(
                                            'start_load', ''),
                                        end_load=ld.findtext(
                                            'end_load', '')
                                    )
                                )
                                market.tools.append(tool)
                    exchange.markets.append(market)
            self.exchanges.append(exchange)

    def is_exchange_exists(self, exchange_name: str) -> bool:
        """Проверка существования биржи по полному имени."""
        return any(
            ex.parameters.full_name.lower() == exchange_name.lower()
            for ex in self.exchanges
        )

    def is_market_exists(self, exchange_name: str, market_name: str) -> bool:
        """Проверка существования рынка на конкретной бирже."""
        for ex in self.exchanges:
            name = ex.parameters.full_name.lower()
            if name == exchange_name.lower():
                return any(
                    m.parameters.full_name.lower() == market_name.lower()
                    for m in ex.markets
                )
        return False

    def is_tool_exists(self, exchange_name: str, market_name: str,
                       tool_name: str) -> bool:
        """Проверка наличия инструмента в заданном рынке и бирже."""
        return self._find_tool_model(exchange_name, market_name,
                                     tool_name) is not None

    def get_exchange_names(self) -> List[str]:
        """Получение списка названий всех бирж."""
        return [ex.parameters.full_name for ex in self.exchanges]

    def get_path_load_for_exchange(self, exchange_name: str) -> Optional[str]:
        """Получение пути загрузки для указанной биржи."""
        for ex in self.exchanges:
            name = ex.parameters.full_name.lower()
            if name == exchange_name.lower():
                return ex.parameters.path_load
        return None

    def get_markets_for_exchange(self,
                                 exchange_name: str) -> Optional[List[str]]:
        """Получение списка рынков для указанной биржи."""
        for ex in self.exchanges:
            name = ex.parameters.full_name.lower()
            if name == exchange_name.lower():
                return [m.parameters.full_name for m in ex.markets]
        return None

    def get_tools_for_market(self, exchange_name: str,
                             market_name: str) -> Optional[List[str]]:
        """Получение списка инструментов для указанного рынка."""
        for ex in self.exchanges:
            name = ex.parameters.full_name.lower()
            if name == exchange_name.lower():
                for m in ex.markets:
                    m_name = m.parameters.full_name.lower()
                    if m_name == market_name.lower():
                        return [t.name for t in m.tools]
        return None

    def get_start_date_for_tool(self, exchange_name: str, market_name: str,
                                tool_name: str) -> Optional[str]:
        """Получение даты начала загрузки инструмента."""
        tool = self._find_tool_model(exchange_name, market_name, tool_name)
        return tool.load_date.start_load if tool else None

    def get_end_date_for_tool(self, exchange_name: str, market_name: str,
                              tool_name: str) -> Optional[str]:
        """Получение даты окончания загрузки инструмента."""
        tool = self._find_tool_model(exchange_name, market_name, tool_name)
        return tool.load_date.end_load if tool else None

    def _find_tool_model(self, exchange_name: str, market_name: str,
                         tool_name: str) -> Optional[Tool]:
        """Внутренний поиск объекта инструмента."""
        for ex in self.exchanges:
            if ex.parameters.full_name.lower() == exchange_name.lower():
                for m in ex.markets:
                    m_name = m.parameters.full_name.lower()
                    if m_name == market_name.lower():
                        for t in m.tools:
                            if t.name.upper() == tool_name.upper():
                                return t
        return None

    def update_end_load_date(self, exchange_name: str, market_name: str,
                             tool_name: str, new_date: str) -> bool:
        """Обновление даты окончания загрузки в XML дереве."""
        updated = False
        for exch in self.root.findall('exchange'):
            ex_n = exch.find('parameters/full_name')
            if (ex_n is not None and
                    ex_n.text.lower() == exchange_name.lower()):
                for mkt in exch.findall('markets/market'):
                    mk_n = mkt.find('parameters/full_name')
                    if (mk_n is not None and
                            mk_n.text.lower() == market_name.lower()):
                        for tool in mkt.findall('tools/tool'):
                            tl_n = tool.find('name')
                            if (tl_n is not None and
                                    tl_n.text.upper() ==
                                    tool_name.upper()):
                                end_ld = tool.find('load_date/end_load')
                                if end_ld is not None:
                                    end_ld.text = new_date
                                    updated = True
        if updated:
            self._refresh_model()
        return updated

    def save_changes(self, output_path: Optional[str] = None) -> None:
        """Сохранение текущего состояния XML в файл."""
        path = output_path if output_path else self.file_path
        self.tree.write(path, encoding='utf-8', xml_declaration=True)

    def get_full_xml_string(self) -> str:
        """Получение XML структуры в виде форматированной строки."""
        raw_xml = ET.tostring(self.root, encoding='utf-8')
        parsed = minidom.parseString(raw_xml)
        return parsed.toprettyxml(indent="  ")

