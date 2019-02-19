"""
MENI TREBA:
    <koje predmete slusa, na kom smeru> [kod kojih profesora]

PEDJI JEDINO TREBA:
    formula koja kaze da on K termina necega sme da se slusa TACNO jedan
    da da niz t/f i da kaze tacno netacno
    ----||------ vrati niz time-unita

PEDJI NE TREBA:
    preklapanje predavanja, to NE TREBA da bude u formuli

"""
import os
from timetable_parser.timetable_unit import timetable_unit
from sqlalchemy import create_engine, MetaData, Table, and_
from sqlalchemy.engine import ResultProxy
from sqlalchemy.sql import select
from itertools import combinations
import subprocess

def sqlite_connection_str(path: str)->str:
    """ :param path - absolute path to db or :memory: for in memory db"""
    return f'sqlite:///{path}'

def parse_input():
    lectures = []

    #smer
    course = ''
    with open("test_input.txt", "r") as f:
        course = f.readline().strip()
        for line in f.readlines():
            lectures.append(line.strip())
    return(course, lectures)



def build_query(courses:str, lectures:list, m:MetaData):
    
    timetable: Table = m.tables['timetable']
    groups: Table = m.tables['groups']
    professors: Table = m.tables['professors']
    rooms: Table = m.tables['rooms']
    subjects: Table = m.tables['subjects']
    types: Table = m.tables['types']

    t = timetable.join(subjects, subjects.c.subject_id == timetable.c.subject_id)\
    .join(groups, timetable.c.group_id == groups.c.group_id)\
    .join(professors, timetable.c.teacher_id == professors.c.professor_id)\
    .join(rooms, timetable.c.room_id == rooms.c.room_id)\
    .join(types, timetable.c.type_id == types.c.type_id)
    #TODO resiti problem gde ce group_str da izdvoji 4I i 4IMAS, ali treba da izdvoji 1O1 i 1O2 VALJDA
    #select * from groups where name GLOB '?И[0-9]*'; ali ovo ne matchuje 4И ni 4ИМАС
    group_names = courses.strip().split(" ")
    #group_str = f'_{course}[0-9]%'

    sel = select(
                    [
                        groups.c.name, timetable.c.day, timetable.c.time_start, timetable.c.time_finish,
                        subjects.c.name, types.c.name, professors.c.name, rooms.c.name
                    ]
                )\
        .where(and_(timetable.c.teacher_id != None,
                    subjects.c.name.in_( lectures ),
                    groups.c.name.in_(group_names)))\
        .select_from(t)\
    
    #  print(sel)
    return sel 


def main():
    db_path = os.path.join(os.path.realpath('.'), 'db.sqlite')
    engine = create_engine(sqlite_connection_str(db_path))

    m = MetaData()
    m.reflect(engine)

    conn = engine.connect()

    (course, lectures) = parse_input()
    
    sel = build_query(course, lectures, m)


    #TODO razdvojiti prve i druge vezbe(ako postoje)
    #    0              1                   2                       3
    #  groups.c.name, timetable.c.day, timetable.c.time_start, timetable.c.time_finish,
    #       4               5               6               7
    #  subjects.c.name, types.c.name, professors.c.name, rooms.c.name
    
    #creating nameType->time dict
    lectures = {}
    res: ResultProxy = conn.execute(sel)
    for i in res:
        lecture_name_type = i[4] + ' ' + i[5]
        if lecture_name_type in lectures:#      day  start end room
            lectures[lecture_name_type].append((i[1],i[2],i[3],i[7]))
        else:
            lectures[lecture_name_type] = [(i[1],i[2],i[3],i[7])]
    output_string : str = ''

    #creating maping for nameTypeTime->int
    lecture_maping = {}
    lecture_maping_inverse = {}
    i=1
    for (name,time) in lectures.items():
        for t in time:
            lecture_maping[name+str(t)] = i
            lecture_maping_inverse[i] = name+str(t)
            i+=1
    #  print(lecture_maping)

    for (name, times) in lectures.items():
        for t in times:
            output_string += ''+str(lecture_maping[name+str(t)]) + ' '
        output_string += '0\n'
        combs = combinations(times, len(times)-1)
        if len(times) > 2:
            for c in combs:
                for t in c:
                    output_string += '-'+str(lecture_maping[name+str(t)]) + ' '
                output_string += '0\n'
        elif len(times) == 2:
            output_string += '-' + str(lecture_maping[name+str(times[0])]) + ' -' + str(lecture_maping[name+str(times[1])]) + ' 0\n'

    #NOTE dovde je kodirano da svako predavanje mora da se slusa tacno jednom
    #sledece treba uraditi preklapanja termina
    #  print ( output_string )

    
    #preklapanje termina
    #NOTE da, prvih 8 ce biti prazno ali idgaf lakse mi ovako
    days = [[None for x in range(21)] for _ in range(5)]
    for (name, time) in lectures.items():
        for t in time:
            for r in range(t[1],t[2]):#za sve termine
                if days[t[0]][r] is None:
                    days[t[0]][r] = [name+str(t)]
                else:
                    days[t[0]][r].append(name+str(t))

    collisions = set()
    for day in days:
        for term in day:
            if term is not None and len(term) > 1:#imamo vise predavanja u jednom termu
                collisions.add("||".join(term)) #moze li ovo eefikasnije?

    for arr in collisions:
        tmp = arr.split("||")
        if len(tmp) > 2:
            combs = combinations(tmp, len(tmp)-1)
            for c in combs:
                for l in c:
                   output_string += ' -' + str(lecture_maping[l])
            output_string += " 0\n"
        elif len(tmp) == 2:
            output_string += '-' + str(lecture_maping[tmp[0]]) + ' -' + str(lecture_maping[tmp[1]]) + ' 0\n'
            

                    
                    
        #  if lecture_name_type in lectures:#      day  start end room
            #  lectures[lecture_name_type].append((i[1],i[2],i[3],i[7]))
             
    
    with open("out.cnf", "w") as f:
        tmp = output_string.strip().split("\n")
        print(tmp)
        f.write(f"p cnf {i-1} {len(tmp)}\n\n")
        f.writelines(output_string)

    subprocess.run(["minisat", "out.cnf", "solution.txt"])
    with open("solution.txt", "r") as f:
        solved = f.readline()
        if solved.strip() == "SAT":
            solution = f.readline()
            solution = solution.split(" ")
            solution = solution[:-1]
            for s in solution:
                if s[0] == '-':
                    print("NOT ", end = "")
                    print(lecture_maping_inverse[int(s[1:])])
                else:
                    print(lecture_maping_inverse[int(s)])

        else:
            print("UNSAT")


    
        



if __name__ == "__main__":
    main()
