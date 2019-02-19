import os
from sqlalchemy import create_engine, MetaData, Table, and_
from sqlalchemy.engine import ResultProxy
from sqlalchemy.sql import select

from bs4 import BeautifulSoup as bs
from bs4 import Tag

def sqlite_connection_str(path: str)->str:
    """ :param path - absolute path to db or :memory: for in memory db"""
    return f'sqlite:///{path}'


num_to_day = {'0':'Ponedeljak', '1': 'Utorak', '2': 'Sreda', '3': 'Cetvrtak', '4': 'Petak'}

def main():
    db_path = os.path.join(os.path.realpath('.'), 'db.sqlite')
    engine = create_engine(sqlite_connection_str(db_path))

    m = MetaData()
    m.reflect(engine)

    timetable: Table = m.tables['timetable']
    groups: Table = m.tables['groups']
    professors: Table = m.tables['professors']
    rooms: Table = m.tables['rooms']
    subjects: Table = m.tables['subjects']
    types: Table = m.tables['types']

    conn = engine.connect()

    t = timetable.join(subjects, subjects.c.subject_id == timetable.c.subject_id)\
    .join(groups, timetable.c.group_id == groups.c.group_id)\
    .join(professors, timetable.c.teacher_id == professors.c.professor_id)\
    .join(rooms, timetable.c.room_id == rooms.c.room_id)\
    .join(types, timetable.c.type_id == types.c.type_id)

    sel = select(
                    [
                        groups.c.name, timetable.c.day, timetable.c.time_start, timetable.c.time_finish,
                        subjects.c.name, types.c.name, professors.c.name, rooms.c.name
                    ]
                )\
        .where(timetable.c.teacher_id != None)\
        .select_from(t)\

    res: ResultProxy = conn.execute(sel)

    group_map= {}
    for i in res:
        if i[0] not in group_map:
            group_map[i[0]] = {}

        if str(i[1]) not in group_map[i[0]]:
            group_map[i[0]][str(i[1])] = []

        group_map[i[0]][str(i[1])].append(make_unit(i))

    path = os.path.join('.', 'raspored')

    if not os.path.exists(path):
        os.mkdir(path)

    for group, data in group_map.items():
        make_group_html(group, data)

    res.close()

def make_group_html(group, data):
    soup = bs('', 'html.parser')

    table = soup.new_tag('table')
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

    header = soup.new_tag('tr')
    for i in range(14):
        time = soup.new_tag('td')
        if i != 0:
            time.append(soup.new_string(f'{7+i}-{8+i}'))
        header.append(time)
    table.append(header)

    for day, day_data in data.items():
        make_day(day, day_data, soup, table)

    with open(os.path.join('.', 'raspored', f'{group}.html'), 'w') as f:
        f.write(soup.prettify())

def make_day(day, data, soup: bs, tag: Tag):
    rows_indicator = [[False for i in range(13)]]
    rows = []

    for unit in data:
        row_index = fit_in_row(rows_indicator, unit['time_start'], unit['time_finish'])
        if row_index >= len(rows):
            rows.append([unit])
        else:
            rows[row_index].append(unit)


    for i, row in enumerate(rows):
        row_tag = soup.new_tag('tr')
        if i == 0:
            td = soup.new_tag('td', attrs={'rowspan':len(rows)})
            td.append(soup.new_string(num_to_day[day]))
            row_tag.append(td)

        tag.append(row_tag)
        make_row(row, soup, row_tag)



def fit_in_row(rows_indicator, time_start, time_finish):
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

def make_row(data, soup: bs, tag: Tag):
    current_time = 8

    for i in data:
        while current_time < i['time_start']:
            td = soup.new_tag('td')
            td.attrs['class'] = 'inner'
            tag.append(td)
            current_time += 1
        td = soup.new_tag('td', attrs={'colspan':i['time_finish']-i['time_start']})
        td.attrs['class'] = 'inner'

        pre = soup.new_tag('pre')
        pre.append(soup.new_string(f'{i["subject"]}\n{i["type"]}\n{i["teacher"]}\n{i["room"]}'))


        td.append(pre)
        tag.append(td)
        current_time = i['time_finish']

    while current_time < 21:
        td = soup.new_tag('td')
        td.attrs['class'] = 'inner'
        tag.append(td)
        current_time += 1



def make_unit(row):
    names = ['group', 'day', 'time_start', 'time_finish', 'subject', 'type', 'teacher', 'room']
    res = {}
    for i, name in enumerate(names):
       res[name] =  row[i]

    return res

if __name__ == '__main__':
    main()



