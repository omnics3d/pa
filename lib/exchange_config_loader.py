import sys
import os
import json

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

def get_full_names_of_all_exchanges() -> list[str]:
    """получить полные имена всех бирж

    :return: список полных имён всех бирж
    :rtype: list[str]
    """
    data = _load_json_data()
    if isinstance(data['exchanges']['exchange'], list):
        return [exchange['parameters']['full_name'] for exchange in data['exchanges']['exchange']]
    else:
        return [data['exchanges']['exchange']['parameters']['full_name']]

def get_full_names_of_all_markets(exchange: str) -> list[str]:
    """получить полные имена всех рынков заданой биржи

    :param exchange: наименование биржы, все рынки которой необходимо получить
    :type exchange: str
    :return: список полных имён всех рынков
    :rtype: list[str]
    """
    exchange_data = _get_exchange_data(exchange)
    markets = exchange_data['markets']['market']
    if isinstance(markets, list):
        return [market['parameters']['full_name'] for market in markets]
    else:
        return [markets['parameters']['full_name']]

def get_names_all_tools(exchange: str, market: str) -> list[str]:
    """получить все инструменты

    :param exchange: наименование биржы, инструменты которой нужно получить
    :type exchange: str
    :param market: наименование рынка, инструменты которого нужно получить
    :type market: str
    :return: наименование всех инструментов
    :rtype: list[str]
    """
    market_data = _get_market_data(exchange, market)
    tools = market_data['tools']['tool']
    if isinstance(tools, list):
        return [tool['name'] for tool in tools]
    else:
        return [tools['name']]

def get_tool_end_date_load(exchange: str, market: str, tool: str) -> str:
    """получить дату окончания загрузки инструмента

    :param exchange: наименование биржы, даты загрузки инструмента которой
        необходимо получить
    :type exchange: str
    :param market: наименование рынка, даты загрузки инструмента которого
        необходимо получить
    :type market: str
    :param tool: наименование инструмента, даты загрузки которого надо получить
    :type tool: str
    :return: возвращает дату начала или дату окончания загрузки в зависимости
        от полученого параметра
    :rtype: str
    """
    tool_data = _get_tool_data(exchange, market, tool)
    return tool_data['load_date']['end_load']

def get_tool_start_date_load(exchange: str, market: str, tool: str) -> str:
    """получить дату начала загрузки инструмента

    :param exchange: наименование биржы, даты загрузки инструмента которой
        необходимо получить
    :type exchange: str
    :param market: наименование рынка, даты загрузки инструмента которого
        необходимо получить
    :type market: str
    :param tool: наименование инструмента, даты загрузки которого надо получить
    :type tool: str
    :return: возвращает дату начала или дату окончания загрузки в зависимости
        от полученого параметра
    :rtype: str
    """
    tool_data = _get_tool_data(exchange, market, tool)
    return tool_data['load_date']['start_load']

def get_path_load(exchange: str) -> str:
    """получить путь загрузки данных биржи

    :param exchange: наименование биржи, путь загрузки данных которой нужно
        получить
    :type exchange: str
    :return: html путь загрузки
    :rtype: str
    """
    exchange_data = _get_exchange_data(exchange)
    return exchange_data['parameters']['path_load']

def check_the_full_name_of_the_exchange(exchange: str) -> bool:
    """проверка полного имени биржи

    Проверяет полученое имя на наличие такого же в списке бирж json файла.

    :param exchange: имя для проверки
    :type exchange: str
    :return: **true** или **false** в зависимости от проверки
    :rtype: bool
    """
    return exchange in get_full_names_of_all_exchanges()

def check_the_full_name_of_the_market(exchange: str, market: str) -> bool:
    """проверка полного имени рынка заданой биржи

    Проверяет полученое имя на наличие такого же в списке рынков заданой
    биржи json файла.

    :param exchange: имя биржи, имена рынков которой проверяются
    :type exchange: str
    :param market: имя рынка для проверки
    :type market: str
    :return: **true** или **false** в зависимости от проверки
    :rtype: bool
    """
    return market in get_full_names_of_all_markets(exchange)

def check_the_full_name_of_the_tool(exchange: str, market: str, tool: str) -> bool:
    """проверка имени инструмента

    Проверяет полученое имя на наличие такого же в списке инструментов заданой
    биржи json файла.

    :param exchange: наименование биржи, инструмент которой проверяются
    :type exchange: str
    :param market: наименование рынка, инструмент которого проверяется
    :type market: str
    :param tool: наименование инструмента для проверки
    :type tool: str
    :return: **true** или **false** в зависимости от проверки
    :rtype: bool
    """
    return tool in get_names_all_tools(exchange, market)

def save_end_date_load(exchange: str, market: str, tool: str, date: str):
    """сохранить дату последнего загруженного файла

    :param exchange: биржа с которой производится загрузка
    :type exchange: str
    :param market: рынок с которого производится загрузка
    :type market: str
    :param tool: загружаемый инструмент
    :type tool: str
    :param date: дата последнего загруженного дня
    :type date: str
    """
    data = _load_json_data()
    
    # Находим и обновляем дату
    tool_data = _find_tool_in_data(data, exchange, market, tool)
    if tool_data:
        tool_data['load_date']['end_load'] = date
        
        # Сохраняем обновленные данные
        with open('config/exchanges_config.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def _load_json_data() -> dict:
    """загрузить данные из JSON файла

    :return: данные из JSON файла
    :rtype: dict
    """
    with open('config/exchanges_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def _get_exchange_data(exchange: str) -> dict:
    """получить данные биржи

    :param exchange: наименование биржи
    :type exchange: str
    :return: данные биржи
    :rtype: dict
    """
    data = _load_json_data()
    exchanges = data['exchanges']['exchange']
    
    if isinstance(exchanges, list):
        for exch in exchanges:
            if exch['parameters']['full_name'] == exchange:
                return exch
    else:
        if exchanges['parameters']['full_name'] == exchange:
            return exchanges
    
    raise ValueError(f"Биржа {exchange} не найдена")

def _get_market_data(exchange: str, market: str) -> dict:
    """получить данные рынка

    :param exchange: наименование биржи
    :type exchange: str
    :param market: наименование рынка
    :type market: str
    :return: данные рынка
    :rtype: dict
    """
    exchange_data = _get_exchange_data(exchange)
    markets = exchange_data['markets']['market']
    
    if isinstance(markets, list):
        for mkt in markets:
            if mkt['parameters']['full_name'] == market:
                return mkt
    else:
        if markets['parameters']['full_name'] == market:
            return markets
    
    raise ValueError(f"Рынок {market} не найден в бирже {exchange}")

def _get_tool_data(exchange: str, market: str, tool: str) -> dict:
    """получить данные инструмента

    :param exchange: наименование биржи
    :type exchange: str
    :param market: наименование рынка
    :type market: str
    :param tool: наименование инструмента
    :type tool: str
    :return: данные инструмента
    :rtype: dict
    """
    market_data = _get_market_data(exchange, market)
    tools = market_data['tools']['tool']
    
    if isinstance(tools, list):
        for t in tools:
            if t['name'] == tool:
                return t
    else:
        if tools['name'] == tool:
            return tools
    
    raise ValueError(f"Инструмент {tool} не найден в рынке {market} биржи {exchange}")

def _find_tool_in_data(data: dict, exchange: str, market: str, tool: str) -> dict:
    """найти данные инструмента в структуре данных

    :param data: данные JSON
    :type data: dict
    :param exchange: наименование биржи
    :type exchange: str
    :param market: наименование рынка
    :type market: str
    :param tool: наименование инструмента
    :type tool: str
    :return: данные инструмента или None если не найден
    :rtype: dict
    """
    exchanges = data['exchanges']['exchange']
    
    if isinstance(exchanges, list):
        for exch in exchanges:
            if exch['parameters']['full_name'] == exchange:
                markets = exch['markets']['market']
                if isinstance(markets, list):
                    for mkt in markets:
                        if mkt['parameters']['full_name'] == market:
                            tools = mkt['tools']['tool']
                            if isinstance(tools, list):
                                for t in tools:
                                    if t['name'] == tool:
                                        return t
                            else:
                                if tools['name'] == tool:
                                    return tools
                else:
                    if markets['parameters']['full_name'] == market:
                        tools = markets['tools']['tool']
                        if isinstance(tools, list):
                            for t in tools:
                                if t['name'] == tool:
                                    return t
                        else:
                            if tools['name'] == tool:
                                return tools
    else:
        if exchanges['parameters']['full_name'] == exchange:
            markets = exchanges['markets']['market']
            if isinstance(markets, list):
                for mkt in markets:
                    if mkt['parameters']['full_name'] == market:
                        tools = mkt['tools']['tool']
                        if isinstance(tools, list):
                            for t in tools:
                                if t['name'] == tool:
                                    return t
                        else:
                            if tools['name'] == tool:
                                return tools
            else:
                if markets['parameters']['full_name'] == market:
                    tools = markets['tools']['tool']
                    if isinstance(tools, list):
                        for t in tools:
                            if t['name'] == tool:
                                return t
                    else:
                        if tools['name'] == tool:
                            return tools
    
    return None

if __name__ == "__main__":
    print(get_path_load("bybit"))
