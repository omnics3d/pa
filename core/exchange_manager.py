import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class LoadDate:
    start_load: str
    end_load: str


@dataclass
class Tool:
    name: str
    load_date: LoadDate
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketParameters:
    full_name: str
    short_name: str
    rus_name: str


@dataclass
class Market:
    parameters: MarketParameters
    tools: List[Tool] = field(default_factory=list)


@dataclass
class ExchangeParameters:
    full_name: str
    short_name: str
    rus_name: str
    path_load: str


@dataclass
class Exchange:
    parameters: ExchangeParameters
    markets: List[Market] = field(default_factory=list)


class ExchangeDataManager:
    def __init__(self, xml_file_path: str) -> None:
        self.file_path = xml_file_path
        self.tree = ET.parse(xml_file_path)
        self.root = self.tree.getroot()
        self.exchanges: List[Exchange] = []
        self._refresh_model()

    def _refresh_model(self) -> None:
        self.exchanges = []
        for ex_el in self.root.findall("exchange"):
            p = ex_el.find("parameters")
            if p is None:
                continue
            ex_params = ExchangeParameters(
                full_name=p.findtext("full_name", ""),
                short_name=p.findtext("short_name", ""),
                rus_name=p.findtext("rus_name", ""),
                path_load=p.findtext("path_load", ""),
            )
            exchange = Exchange(parameters=ex_params)
            m_node = ex_el.find("markets")
            if m_node is not None:
                for mk_el in m_node.findall("market"):
                    mp = mk_el.find("parameters")
                    if mp is None:
                        continue
                    m_params = MarketParameters(
                        full_name=mp.findtext("full_name", ""),
                        short_name=mp.findtext("short_name", ""),
                        rus_name=mp.findtext("rus_name", ""),
                    )
                    market = Market(parameters=m_params)
                    t_node = mk_el.find("tools")
                    if t_node is not None:
                        for tl_el in t_node.findall("tool"):
                            ld = tl_el.find("load_date")
                            if ld is not None:
                                tool = Tool(
                                    name=tl_el.findtext("name", ""),
                                    load_date=LoadDate(
                                        start_load=ld.findtext("start_load", ""),
                                        end_load=ld.findtext("end_load", ""),
                                    ),
                                )
                                market.tools.append(tool)
                    exchange.markets.append(market)
            self.exchanges.append(exchange)

    def get_exchange_names(self) -> List[str]:
        return [ex.parameters.full_name for ex in self.exchanges]

    def get_markets_for_exchange(self, exchange_name: str) -> Optional[List[str]]:
        for ex in self.exchanges:
            if ex.parameters.full_name.lower() == exchange_name.lower():
                return [m.parameters.full_name for m in ex.markets]
        return None

    def get_tools_for_market(
        self, exchange_name: str, market_name: str
    ) -> Optional[List[str]]:
        for ex in self.exchanges:
            if ex.parameters.full_name.lower() == exchange_name.lower():
                for m in ex.markets:
                    if m.parameters.full_name.lower() == market_name.lower():
                        return [t.name for t in m.tools]
        return None

    def get_tool_data_path(
        self, exchange_name: str, market_name: str, tool_name: str
    ) -> Optional[str]:
        tool = self._find_tool_model(exchange_name, market_name, tool_name)
        return f"data/{exchange_name}/{market_name}/{tool.name}" if tool else None

    def get_start_date_for_tool(
        self, exchange_name: str, market_name: str, tool_name: str
    ) -> Optional[str]:
        tool = self._find_tool_model(exchange_name, market_name, tool_name)
        return tool.load_date.start_load if tool else None

    def get_end_date_for_tool(
        self, exchange_name: str, market_name: str, tool_name: str
    ) -> Optional[str]:
        tool = self._find_tool_model(exchange_name, market_name, tool_name)
        return tool.load_date.end_load if tool else None

    def _find_tool_model(
        self, exchange_name: str, market_name: str, tool_name: str
    ) -> Optional[Tool]:
        for ex in self.exchanges:
            if ex.parameters.full_name.lower() == exchange_name.lower():
                for m in ex.markets:
                    if m.parameters.full_name.lower() == market_name.lower():
                        for t in m.tools:
                            if t.name.upper() == tool_name.upper():
                                return t
        return None
