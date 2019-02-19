import typing as ty
from bs4 import BeautifulSoup as bs
from bs4 import Tag
from timetable_parser.parser import  timetable_unit

__num_to_day = {'0':'Ponedeljak', '1': 'Utorak', '2': 'Sreda', '3': 'Cetvrtak', '4': 'Petak'}

def timetable_to_html(lessons: ty.List[timetable_unit], get_text: ty.Callable[[timetable_unit], str],
                      prettify: bool = True)->str:
    """

    :param lessons: list of lessons to put in table
    :param get_text: callable that returns string from timetable this will be text in a cell
    :param prettify: should it be prettified
    :return: html string of timetable
    """
    days = [list() for i in range(5)]

    for unit in lessons:
        days[unit.day].append(unit)

    soup = bs('', 'html.parser')
    table  = soup.new_tag('table')
    soup.append(table)
    style = soup.new_tag('style')
    style.append(soup.new_string("""
        table 
        {
            border-collapse:collapse;
            width:100%;
        }
        td
        {
        
            border:1px solid black;
            text-align:center;
        }
        .inner
        {
            width:7.69%;
        }
    """))

    soup.append(style)

    row = soup.new_tag('tr')
    table.append(row)

    for i in range(14):
        td = soup.new_tag('td')
        row.append(td)
        if i != 0:
            td.append(soup.new_string(f'{7+i:02d}-{8+i:02d}'))

    for i, day in enumerate(days):
        day.sort(key=lambda x: x.start_time)
        __make_day(i, day, soup, table, get_text)

    if prettify:
        return soup.prettify()
    else:
        return str(soup)



def __make_day(day: int, data: ty.List[timetable_unit], soup: bs, element: Tag,
               get_text:ty.Callable[[timetable_unit], str]):
    rows_indicator = [[False for i in range(13)]]
    rows = []

    for unit in data:
        row_index = __fit_in_row(rows_indicator, unit.start_time , unit.finish_time)
        if row_index >= len(rows):
            rows.append([unit])
        else:
            rows[row_index].append(unit)

    for i, row in enumerate(rows):
        row_tag = soup.new_tag('tr')
        if i == 0:
            td = soup.new_tag('td', attrs={'rowspan':len(rows)})
            td.append(soup.new_string(__num_to_day[str(day)]))
            row_tag.append(td)

        element.append(row_tag)
        __make_row(row, soup, row_tag, get_text)


def __make_row(data: ty.List[timetable_unit], soup: bs, element: Tag, get_text: ty.Callable[[timetable_unit], str]):
    current_time = 8

    for i in data:
        while current_time < i.start_time:
            td = soup.new_tag('td')
            td.attrs['class'] = 'inner'
            element.append(td)
            current_time += 1
        td = soup.new_tag('td', attrs={'colspan':i.finish_time-i.start_time})
        td.attrs['class'] = 'inner'

        pre = soup.new_tag('pre')
        pre.append(soup.new_string(get_text(i)))

        td.append(pre)
        element.append(td)
        current_time = i.finish_time

    while current_time < 21:
        td = soup.new_tag('td')
        td.attrs['class'] = 'inner'
        element.append(td)
        current_time += 1


def __fit_in_row(rows_indicator: ty.List[ty.List[bool]] , time_start: int, time_finish: int):
    for i in range(len(rows_indicator)):
        for j in range(time_start - 8, time_finish-8):
            if rows_indicator[i][j] != False:
                break
        else:
            for j in range(time_start - 8, time_finish-8):
                rows_indicator[i][j] = True
            return i

    rows_indicator.append([False for i in range(13)])
    for j in range(time_start - 8, time_finish-8):
        rows_indicator[-1][j] = True

    return len(rows_indicator)-1


