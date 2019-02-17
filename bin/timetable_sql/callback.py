import typing as ty
from timetable_parser.timetable_unit import timetable_unit
from timetable_parser.utils import lecture_enum

from sqlalchemy import create_engine
from sqlalchemy import MetaData, Table, Column, Integer, VARCHAR, ForeignKey
from sqlalchemy.sql import Insert
from sqlalchemy.engine.result import  ResultProxy


class callback:
    def __init__(self, engine_url: str, table_prefix: str = ''):
        self.rooms = set()
        self.subjects = set()
        self.professors = set()
        self.groups = set()
        self.days = []
        self.day = []
        self.engine_url = engine_url
        self.table_prefix = table_prefix


    def __call__(self, unit: timetable_unit):
        if len(self.days) != unit.day:
            self.days.append(self.day)
            self.day = []


        self.rooms.add(unit.room)
        self.subjects.add(unit.subject)
        if unit.teacher is not None:
            self.professors.add(unit.teacher)
        self.groups.add(unit.group)

        i:timetable_unit
        for i in self.day:
            if i.finish_time == unit.start_time and i.hash == unit.hash:
                i.finish_time = unit.finish_time
                break
        else:
            self.day.append(unit)



    def write_to_db(self):
        engine = create_engine(self.engine_url)

        conn = engine.connect()
        m = MetaData()


        if self.table_prefix != '':
            self.table_prefix = self.table_prefix + '_'

        rooms = Table(f'{self.table_prefix}rooms', m,
                      Column('room_id', Integer, primary_key=True),
                      Column('name', VARCHAR(10), nullable=False)
                      )
        subjects = Table(f'{self.table_prefix}subjects', m,
                         Column('subject_id', Integer, primary_key=True) ,
                         Column('name', VARCHAR(50), nullable=False)
                         )

        professors = Table(f'{self.table_prefix}professors', m,
                           Column('professor_id', Integer, primary_key=True),
                           Column('name', VARCHAR(100), nullable=False)
                           )

        groups = Table(f'{self.table_prefix}groups', m,
                       Column('group_id', Integer, primary_key=True),
                       Column('name', VARCHAR(10), nullable=False)
                       )

        types = Table(f'{self.table_prefix}types', m,
                      Column('type_id', Integer, primary_key=True, autoincrement=False),
                      Column('name', VARCHAR(10), nullable=False)
                      )

        timetable = Table(f'{self.table_prefix}timetable', m,
                          Column('day', Integer, primary_key=True, autoincrement=False),
                          Column('time_start', Integer, primary_key=True, autoincrement=False),
                          Column('room_id', Integer, ForeignKey(f'{self.table_prefix}rooms.room_id'), primary_key=True),
                          Column('time_finish', Integer, nullable=False),
                          Column('subject_id', Integer, ForeignKey(f'{self.table_prefix}subjects.subject_id'),
                                 nullable=False),
                          Column('type_id', Integer, ForeignKey(f'{self.table_prefix}types.type_id'), nullable=False),
                          Column('group_id', Integer, ForeignKey(f'{self.table_prefix}groups.group_id'), primary_key=True),
                          Column('teacher_id', Integer, ForeignKey(f'{self.table_prefix}professors.professor_id')),
                          Column('sub_group', VARCHAR(20))
                          )

        m.drop_all(engine)
        m.create_all(engine)

        ins: Insert = rooms.insert()
        rooms_mapping = {}
        for room in self.rooms:
            res: ResultProxy = conn.execute(ins, name=room)
            rooms_mapping[room] = res.inserted_primary_key[0]

        ins = subjects.insert()
        subjects_mapping = {}
        for subject in self.subjects:
            res: ResultProxy = conn.execute(ins, name=subject)
            subjects_mapping[subject] = res.inserted_primary_key[0]

        ins = professors.insert()
        professors_mapping = {}
        for professor in self.professors:
            res: ResultProxy = conn.execute(ins, name=professor)
            professors_mapping[professor] = res.inserted_primary_key[0]

        ins = groups.insert()
        groups_mapping= {}
        for group in self.groups:
            res: ResultProxy = conn.execute(ins, name=group)
            groups_mapping[group] = res.inserted_primary_key[0]

        ins = types.insert()
        conn.execute(ins, type_id=lecture_enum.LECTURE, name='Predavanja')
        conn.execute(ins, type_id=lecture_enum.PRACTICE , name='Praktikum')
        conn.execute(ins, type_id=lecture_enum.PRACTICAL, name='Vezbe')

        ins = timetable.insert()
        self.days.append(self.day)
        self.day = []

        unit: timetable_unit
        for day in self.days:
            for unit in day:
                conn.execute(ins, day=unit.day, time_start=unit.start_time, room_id=rooms_mapping[unit.room],
                             time_finish=unit.finish_time, subject_id=subjects_mapping[unit.subject],
                             type_id=unit.type, group_id=groups_mapping[unit.group],
                             teacher_id=None if unit.teacher is None else professors_mapping[unit.teacher],
                             sub_group=(None if unit.sub_group is None else ','.join(unit.sub_group)))



def mysql_connection_str()->str:
    pass


def sqlite_connection_str(path: str)->str:
    """ :param path - absolute path to db or :memory: for in memory db"""
    return f'sqlite:///{path}'
