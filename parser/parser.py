import sys
import logging
import hashlib
import requests as r
from bs4 import BeautifulSoup as bs
import bs4

import typing as ty

callback_T = ty.Callable[[str, int, str, str, ty.Optional[ty.List[str]], str, str], None]
logger = logging.getLogger(__name__)


class lecture_enum:
    LECTURE: int = 0
    PRACTICAL: int = 1
    PRACTICE: int = 2


class parser:
    def __init__(self, base_url: str, recursive: bool = False):
        """
        :param  base_url - url to parse
        :param recursive - should parser follow other groups
        """

        self.base_url = base_url
        self.should_follow = recursive

        # rfind could return - 1 but this will probably not happen
        if self.base_url.rfind('/') == len(self.base_url) - 1:
            self.base_url = self.base_url[0:len(self.base_url) - 1]

        self.base_template = self.base_url[0:self.base_url.rfind('/')]

    def __parse_the_page(self, callback: callback_T, soup: bs):
        current_day = 0
        current_time = 8

        rows = get_all_rows(soup)

        group = get_group(soup)

        for i, row in enumerate(rows):
            current_time = 8
            logger.debug('Parsing row %s', i)
            cells = get_all_cells(row)

            for j, cell in enumerate(cells):
                logger.debug('Parsing cell %s', j)
                current_time += parse_cell(cell, callback, current_time, current_day, group)

            current_day += 1

    def parse(self, callback: callback_T):
        """
        :param  callback is callable object or function that receives next arguments
                subject:str  - subject name
                type: int - lecture type 0 - lecture 1 - practical 2 - practice constants can be found in class
                lecture_enum
                teacher: str - name of the teacher
                group: str - name of the group
                sub_group: Optional[List[str]] - optional sub group
                room: str - room that lecture takes place
                hash: str - hast compare to with others
        """

        response: r.Response = r.get(self.base_url)
        response.encoding = 'UTF-8'

        soup = bs(response.text, 'html.parser')

        if self.should_follow:
            urls = get_all_recursive_url(self.base_template, soup)

        logger.info('Parsing page %s', self.base_url)
        self.__parse_the_page(callback, soup)

        if self.should_follow:
            for url in urls:
                if url != self.base_url:
                    response: r.Response = r.get(url)
                    response.encoding = 'UTF-8'

                    soup = bs(response.text, 'html.parser')

                    logger.info('Parsing page %s', url)
                    self.__parse_the_page(callback, soup)


def get_all_recursive_url(base_template: str, soup: bs) -> ty.List[str]:
    select: bs4.Tag = soup.find('select')
    if select is None:
        logger.critical('Cant find select list for other pages')
        sys.exit(1)

    options: ty.List[bs4.Tag] = select.find_all('option')
    res: ty.List[str] = []

    for option in options:
        if option['value'].endswith('.html'):
            res.append(f'{base_template}/{option["value"]}')

    return res


def get_group(soup: bs) -> str:
    select: bs4.Tag = soup.find('select')
    if select is None:
        logger.critical('Cant find select list for other pages')
        sys.exit(1)

    options: ty.List[bs4.Tag] = select.find_all('option')
    res: str = ''

    for option in options:
        if option.has_attr('selected'):
            res = option.text
            break

    return res


def get_all_rows(soup: bs) -> ty.List[bs4.Tag]:
    table: bs4.Tag = soup.find('table', {'border': '1'})

    if table is None:
        logger.critical('Cant find main table')
        sys.exit(1)

    rows = table.find_all('tr', recursive=False)
    if len(rows) < 7:
        logger.critical('Table has less then 7 rows')
        sys.exit(1)

    return rows[2:]


def get_all_cells(row: bs4.Tag) -> ty.List[bs4.Tag]:
    cells = row.find_all('td', recursive=False)
    if cells is None:
        logger.critical('Row dose not have cells')

    return cells[1:]


def parse_cell(cell: bs4.Tag, callback: callback_T, time: int, day: int, group: str) -> int:

    duration = int(cell['colspan']) if cell.has_attr('colspan') else 1

    table = cell.find('table')
    if table is None:
        logger.debug('cell has no table parsing normally')
        if cell.small is None:
            tmp = cell.contents
            l = len(tmp)
        else:
            tmp = cell.small.contents
            l = len(tmp)

        if l == 5 or l == 7 or l == 4 or l == 6:
            if tmp[0].find('(вежбе)') != -1:
                type = lecture_enum.PRACTICAL
                tmp[0] = tmp[0].replace('(вежбе)', '')
            elif tmp[0].find('(практикум)') != -1:
                type = lecture_enum.PRACTICE
                tmp[0] = tmp[0].replace('(практикум)', '')
            else:
                type = lecture_enum.LECTURE

        hash = hashlib.md5(str(cell).encode('UTF-8')).hexdigest()

        if l == 5:
            callback(day, time, time + duration, tmp[0], type, tmp[2], group, None, tmp[4], hash)
        elif l == 7:
            groups = list(map(lambda x: x.strip(), tmp[2].split(',')))
            #callback(day, time, time + duration, tmp[0], type, tmp[4], group, tmp[2], tmp[6], hash)
            callback(day, time, time + duration, tmp[0], type, tmp[4], group, groups, tmp[6], hash)
        elif l == 4:
            callback(day, time, time + duration, tmp[0], type, None, group, None, tmp[3], hash)
        elif l == 6:
            groups = list(map(lambda x: x.strip(), tmp[2].split(',')))
            #callback(day, time, time + duration, tmp[0], type, None, group, tmp[2], tmp[5], hash)
            callback(day, time, time + duration, tmp[0], type, None, group, groups, tmp[5], hash)
        elif l != 0 and l != 1:
            logger.critical('Found cell with %s content length', l)
            sys.exit(1)

    else:
        logger.debug('cell has table parsing subcells')
        subcells = cell.find_all('td')

        for i in subcells:
            parse_cell(i, callback, time, day, group)

    return duration
