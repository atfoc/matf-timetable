from sqlalchemy.engine.base import Engine
from sqlalchemy import Table, MetaData

def mysql_connection_str(username: str, password: str, host: str, port: str,
                         db_name: str )->str:
    if port != '':
        port = f':{port}'
    if password != '':
        password = f':{password}'
    return f'mysql+pymysql://{username}{password}@{host}{port}/{db_name}'


def sqlite_connection_str(path: str)->str:
    """ :param path - absolute path to db or :memory: for in memory db"""
    return f'sqlite:///{path}'


class database:
    def __init__(self, timetable: Table, groups: Table, professors: Table, rooms: Table,
                 subjects: Table, types:Table, full_view: Table):
        self.timetable = timetable
        self.groups = groups
        self.professors = professors
        self.rooms = rooms
        self.subjects = subjects
        self. types = types
        self.full_view = full_view


def get_database(engine: Engine, prefix: str = '')->database:
    m = MetaData()
    m.reflect(engine)
    if prefix != '':
        prefix = f'{prefix}_'

    timetable: Table = m.tables[f'{prefix}timetable']
    groups: Table = m.tables[f'{prefix}groups']
    professors: Table = m.tables[f'{prefix}professors']
    rooms: Table = m.tables[f'{prefix}rooms']
    subjects: Table = m.tables[f'{prefix}subjects']
    types: Table = m.tables[f'{prefix}types']

    t = timetable.join(subjects, subjects.c.subject_id == timetable.c.subject_id)\
    .join(groups, timetable.c.group_id == groups.c.group_id)\
    .join(professors, timetable.c.teacher_id == professors.c.professor_id)\
    .join(rooms, timetable.c.room_id == rooms.c.room_id)\
    .join(types, timetable.c.type_id == types.c.type_id)

    return database(timetable, groups, professors, rooms, subjects, types, t)