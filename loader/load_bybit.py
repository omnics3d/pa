# {{{
"""Библиотека загрузки минутных свечей

- :ref:`Установка параметров загрузки <1>`
- :ref:`Загрузка ByBit <2>`

Загружает данные минутных свечей заданного инструмента заданой биржи и заданого
рынка.

TODO: Общий алгоритм загрузки
    Главный класс. Или подгрузка всех инструментов, или загрузка 1 инструмента
    с нуля. Не загруженные инструменты определяются по датам - если дата
    окончания загрузки меньше даты начала, то инструмент можно только
    загрузить, подгружаться он не будет.

    Класс загрузки параметров. Потом класс загрузки каждой биржи создаёт в
    себе объект класса загрузки параметров и пользуется свойствами.

    Главный класс в цикле работает с классами загрузки бирж
"""

# }}}

# {{{
""" import
"""
import sys
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from os.path import exists
from os import makedirs
import argparse
import requests
from lib.exchange_config_loader import (
    check_the_full_name_of_the_exchange,
    check_the_full_name_of_the_market,
    check_the_full_name_of_the_tool,
    get_tool_start_date_load,
    get_tool_end_date_load,
    get_full_names_of_all_exchanges,
    get_full_names_of_all_markets,
    get_names_all_tools,
    get_path_load,
    save_end_date_load,
)

# }}}


class SetDownloadOptions:
    # {{{
    """.. _1:

    Установка параметров загрузки


    Устанавливает в свойства класса данные, необходимые для дальнейшей работы,
    предварительно проверив их на валидность.

    :param exchange: наименование биржи
    :type exchange: str
    :param market: наименование рынка
    :type market: str
    :param tool: наименование инструмента
    :type tool: str
    :param start_date_liad: дата начала загрузки инструмента
    :type start_date_load: str
    :param finish_date_load: дата окончания загрузки инструмента
    :type finish_date_load: str
    :param path_load: путь загрузки инструмента
    :type path_load: str
    :param path_save: путь сохранения минутных свечей инструмента
    :type path_save: str
    """

    exchange: str
    market: str
    tool: str
    start_date_load: str
    finish_date_load: str
    now_date: str
    path_load: str
    path_save: str

    def __init__(self, exchange: str, market: str, tool: str):
        self.__check_exchange_param(exchange)
        self.__check_market_param(exchange, market)
        self.__check_tool_param(exchange, market, tool)
        self.__set_start_date_load(exchange, market, tool)
        self.__set_finish_date_load(exchange, market, tool)
        self.__set_now_date()
        self.__set_path_load(exchange)
        self.__set_path_save(exchange, market, tool)

    def __check_exchange_param(self, exchange: str):
        # {{{
        """проверить введённый параметр биржи"""
        if check_the_full_name_of_the_exchange(exchange):
            self.exchange = exchange
        else:
            msg: str = "incorrect exchange name. Optional versions: "
            name_exchange_list: list[str] = get_full_names_of_all_exchanges()
            name: str
            for name in name_exchange_list:
                msg += '"' + name + '" '
            print(msg)
            sys.exit(1)
        # }}}

    def __check_market_param(self, exchange: str, market: str):
        # {{{
        """проверить введённый параметр рынка"""
        if check_the_full_name_of_the_market(exchange, market):
            self.market = market
        else:
            msg: str = "incorrect market name. Optiona versions: "
            name_market_list: list[str] = get_full_names_of_all_markets(exchange)
            name: str
            for name in name_market_list:
                msg += '"' + name + '" '
            print(msg)
            sys.exit(1)
        # }}}

    def __check_tool_param(self, exchange: str, market: str, tool: str):
        # {{{
        """проверить введённый параметр инструмента"""
        if check_the_full_name_of_the_tool(exchange, market, tool):
            self.tool = tool
        else:
            msg: str = "incorrect tool name. Optional versions: "
            name_tool_list: list[str] = get_names_all_tools(exchange, market)
            name: str
            for name in name_tool_list:
                msg += '"' + name + '" '
            print(msg)
            sys.exit(1)
        # }}}

    def __set_start_date_load(self, exchange: str, market: str, tool: str):
        # {{{
        """установить дату начала загрузки

        Установливает в свойство класса строковое представление даты начала
        загрузки рабочего инструмента.

        :param exchange: наименование биржи в которой находится инструмент,
            дату начала загрузки которого необходимо установить.
        :type exchange: str
        :param market: наименование рынка в котором находится инструмент,
            дату начала загрузки которого необходимо установить.
        :type market: str
        :param tool: инструмент, дату начала загрузки которого необходимо
            установить.
        :type tool: str
        """
        start_load: str = get_tool_start_date_load(exchange, market, tool)
        self.start_date_load = start_load
        # }}}

    def __set_finish_date_load(self, exchange: str, market: str, tool: str):
        # {{{
        """установить дату окончания загрузки

        Установливает в свойство класса строковое представление даты окончания
        загрузки рабочего инструмента.

        :param exchange: наименование биржи в которой находится инструмент,
            дату окончания загрузки которого необходимо установить.
        :type exchange: str
        :param market: наименование рынка в котором находится инструмент,
            дату окончания загрузки которого необходимо установить.
        :type market: str
        :param tool: инструмент, дату окончания загрузки которого необходимо
            установить.
        :type tool: str
        """
        finish_load: str = get_tool_end_date_load(exchange, market, tool)
        self.finish_date_load = finish_load
        # }}}

    def __set_now_date(self):
        # {{{
        """установить дату окончания загрузки

        Устанавливает в свойство класса строковое представление даты окончания
        загрузки.
        """
        finish_date_load: datetime.date = datetime.now().date()
        finish_date_load -= timedelta(days=1)
        self.now_date = datetime.strftime(finish_date_load, "%Y-%m-%d")
        # }}}

    def __set_path_load(self, exchange: str):
        # {{{
        """установить путь загрузки данных биржи

        :param exchange: наименование биржи, путь загрузки данных которой
            необходимо получить
        :type exchange: str
        """
        self.path_load = get_path_load(exchange)
        # }}}

    def __set_path_save(self, exchange: str, market: str, tool: str):
        # {{{
        """установить путь сохранения файлов с дневными данными свечей

        :param exchange: наименование биржи для создания одноимённой
            директории
        :type exchange: str
        :param market: наименование рынка, для создания под директории
            в директории биржи
        :type market: str
        :param tool: наименование инструмента для создания под директории
            в директории рынка
        :type tool: str
        """
        self.path_save = "storage/raw/" + exchange + "/" + market + "/" + tool + "/"

        if not exists(self.path_save):
            makedirs(self.path_save, exist_ok=True)
        # }}}

    # }}}


class LoadingBayBit:
    # {{{
    """.. _2:

    загрузка данных ByBit

    Так как на ByBit совсем мало инструментов, данные которых есть сразу в
    файлах, приходится загружать их напрямую с "графика". Класс загружает
    данные блоками, компанует их в дневной блок свечей и сохраняет в
    отведённом месте.

    Использует класс SetDownloadOptions для получения параметров для своей
    работы.
    """

    SDO: SetDownloadOptions
    candle_list: str
    start_datetime: datetime
    end_datetime: datetime

    def __init__(self, exchange: str, market: str, tool: str):
        self.SDO = SetDownloadOptions(exchange, market, tool)

    def start_load(self):
        # {{{
        """Старт загрузки

        Загружает минутные свечи ByBit.
        """
        self.__set_dates_load()
        while self.SDO.start_date_load <= self.SDO.finish_date_load:
            self.__cycle_load_block()
            self.__save_day()
            self.SDO.start_date_load = next_date(self.SDO.start_date_load)
        # }}}

    def __set_dates_load(self):
        # {{{
        """установка дат загрузки"""
        if self.SDO.start_date_load > self.SDO.finish_date_load:
            self.SDO.start_date_load = self.SDO.start_date_load
            self.SDO.finish_date_load = self.SDO.now_date
        else:
            self.SDO.start_date_load = self.SDO.finish_date_load
            self.SDO.start_date_load = next_date(self.SDO.start_date_load)
            self.SDO.finish_date_load = self.SDO.now_date
        # }}}

    def __cycle_load_block(self):
        # {{{
        """цикл загрузки блоков"""
        self.candle_list: str = ""
        self.__set_column_headings()
        self.__set_start_block_day()
        for i in range(0, 8, 1):
            self.__load_block()
            self.__set_time_load_block()
        # }}}

    def __set_column_headings(self):
        # {{{
        """установка заголовков столбцов"""
        column_headings: str = "open_time,open,high,low,close,volume,turnover\n"
        self.candle_list = column_headings
        # }}}

    def __set_start_block_day(self):
        # {{{
        """установка воеменных меток стартового блока загрузки"""
        start_datetime: str = self.SDO.start_date_load + " 00:00:00"
        self.start_datetime = datetime.strptime(
            start_datetime, "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)
        self.end_datetime = self.start_datetime + timedelta(hours=2, minutes=59)
        # }}}

    def __set_time_load_block(self):
        # {{{
        """установка временных меток следующего блока загрузки"""
        self.start_datetime += timedelta(hours=3)
        self.end_datetime = self.start_datetime + timedelta(hours=2, minutes=59)
        # }}}

    def __load_block(self):
        # {{{
        """загрузка блока"""
        start: int = int(self.start_datetime.timestamp()) * 1000
        end: int = int(self.end_datetime.timestamp()) * 1000
        param = {
            "category": self.SDO.market,
            "symbol": self.SDO.tool,
            "interval": "1",
            "start": start,
            "end": end,
            "limit": 180,
        }
        response = requests.get(self.SDO.path_load, params=param)
        self.__sorted_content(response)
        # }}}

    def __sorted_content(self, response: requests.models.Response):
        # {{{
        """сортироваки свечей и подготовка к записи

        :param response: полученный ответ сервера для сортировки
        :type response: requests.models.Response
        """
        sort_list = list(response.json()["result"]["list"])
        sort_list.sort(key=lambda x: x[0])
        for i in sort_list:
            string: str = ",".join(i) + "\n"
            self.candle_list += string
        # }}}

    def __save_day(self):
        # {{{
        """сохранения файла данных свечей за день"""
        name_file: str = self.SDO.tool + "-1m-" + self.SDO.start_date_load + ".csv"
        path: str = self.SDO.path_save + name_file
        with open(path, "w") as file:
            file.write(self.candle_list)
        save_end_date_load(
            self.SDO.exchange,
            self.SDO.market,
            self.SDO.tool,
            self.SDO.start_date_load,
        )
        print("File " + path + " saved", end="\r")
        # print('File ' + name_file + ' saved', end="\r")
        # }}}

    # }}}


def next_date(date: str) -> str:
    # {{{
    """получение следующей даты

    :param date: дата для получения следующего дня
    :type date: str
    :return: дата, следующая за получаемой
    :rtype: str
    """
    start_date: datetime.date = datetime.strptime(date, "%Y-%m-%d").date()
    start_date += timedelta(days=1)
    finish_date: str = datetime.strftime(start_date, "%Y-%m-%d")
    return finish_date
    # }}}


if __name__ == "__main__":
    # {{{
    """Парсер аргументов командной строки"""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Парсер аргументов командной строки"
    )
    parser.add_argument(
        "-e",
        "--exchange",
        type=str,
        default="bybit",
        help="Биржа с которой будет производится загрузка.",
    )
    parser.add_argument(
        "-m",
        "--market",
        type=str,
        default="linear",
        help="Рынок, с которого будет производится загрузка.",
    )
    parser.add_argument(
        "-t", "--tool", type=str, default="DOGEUSDT", help="Инструмент для загрузки."
    )
    agrs: argparse.Namespace = parser.parse_args()
    # }}}
    LB = LoadingBayBit(exchange=agrs.exchange, market=agrs.market, tool=agrs.tool)
    LB.start_load()
