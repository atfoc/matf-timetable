import os
from timetable_parser.timetable_unit import timetable_unit
from sqlalchemy import create_engine, MetaData, Table, and_
from sqlalchemy.engine import ResultProxy
from sqlalchemy.sql import select
from itertools import combinations
from utils.html_writer import timetable_to_html
from dimacs_coder import DimacsCoder
from logic_classes import literal, disjunction
import typing as ty
import subprocess

def sqlite_connection_str(path: str)->str:
    """ :param path - absolute path to db or :memory: for in memory db"""
    return f'sqlite:///{path}'


class FormulaGenerator:
    def __init__(self, filepath : str):
        self.formula : ty.List[disjunction] = []
        self.filepath : str = filepath
        self.groups : str = ''
        self.courses : str = ''
        self.query_result: ResultProxy = None
        self.course_units : ty.Dict[str, timetable_unit] = None
        self.removed_unit : timetable_unit = None
    
    def __parse_input(self):
        courses = []

        #smer
        groups = ''
        with open(self.filepath, "r") as f:
            groups = f.readline().strip()
            for line in f.readlines():
                courses.append(line.strip())

        self.groups = groups
        self.courses = courses

    def __build_query(self, m:MetaData):
        
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
        
        group_names = self.groups.strip().split(" ")

        sel = select(
                        [
                            groups.c.name, timetable.c.day, timetable.c.time_start, timetable.c.time_finish,
                            subjects.c.name, types.c.type_id, professors.c.name, rooms.c.name
                        ]
                    )\
            .where(and_(timetable.c.teacher_id != None,
                        subjects.c.name.in_( self.courses ),
                        groups.c.name.in_(group_names)))\
            .select_from(t)\
        
        #  print(sel)
        return sel 

    def __get_data_from_db(self):
        db_path = os.path.join(os.path.realpath('.'), 'db.sqlite')
        engine = create_engine(sqlite_connection_str(db_path))

        m = MetaData()
        m.reflect(engine)

        conn = engine.connect()
        self.__parse_input()
        query = self.__build_query(m)

        self.query_result: ResultProxy = conn.execute(query)
        self.all_timetable_units = set()
        for result in self.query_result:
            self.all_timetable_units.add(timetable_unit(result[1],result[2],\
                                        result[3],result[4],result[5],result[0],result[7],'hash'))
        self.all_timetable_units = list(self.all_timetable_units)

    def __map_courses_to_units(self):
        self.course_units = {}
        for unit in self.all_timetable_units:
            lecture_name_type : timetable_unit= unit.subject + ' ' + unit.type_text()
            if lecture_name_type in self.course_units:#      day  start end room
                self.course_units[lecture_name_type].append(unit)
            else:
                self.course_units[lecture_name_type] = [unit]


    #YOLO = YOU ONLY LISTEN ONCE
    def __YOLO(self):
        for (name, units) in self.course_units.items():
            disjuncts : ty.List[literal] = []    
            for unit in units:
                disjuncts.append(literal(unit))
            self.formula.append(disjuncts)
            combs = combinations(units, len(units)-1)
            if len(units) > 2:
                for comb in combs:
                    disjuncts : ty.List[literal] = []
                    for unit in comb:
                        disjuncts.append(literal(unit, negated = True))
                    self.formula.append(disjuncts)
            elif len(units) == 2:
                self.formula.append([literal(units[0], negated = True), literal(units[1], negated = True)])

    def __no_course_overlap(self):
        days = [[None for x in range(21)] for _ in range(5)]
        for (name, units) in self.course_units.items():
            for unit in units:
                for r in range(unit.start_time,unit.finish_time):#for complete time span
                    if days[unit.day][r] is None:
                        days[unit.day][r] = [str(unit)]
                    else:
                        days[unit.day][r].append(str(unit))

        collisions = set()
        for day in days:
            for term in day:
                if term is not None and len(term) > 1:#imamo vise predavanja u jednom terminu
                    collisions.add("||".join(term)) #moze li ovo eefikasnije?

        #  print(collisions)
        for arr in collisions:
            tmp = arr.split("||")
            if len(tmp) > 2:
                combs = combinations(tmp, len(tmp)-1)
                for comb in combs:
                    disjuncts : ty.List[literal] = []
                    for l in comb:
                        disjuncts.append(literal(l, negated = True))
                    self.formula.append(disjuncts)
            elif len(tmp) == 2:
                self.formula.append([literal(tmp[0], negated = True), literal(tmp[1], negated = True)])

    def remove_unit(self):
        if self.removed_unit != None:
            self.all_timetable_units.append(self.removed_unit)
        self.course_units = {}
        self.formula = []
        self.removed_unit = self.all_timetable_units[0] 
        print(self.removed_unit)
        self.all_timetable_units.remove(self.removed_unit)

    def code(self):
        #self.removed_unit will be None on the first run
        if self.removed_unit == None:
            self.__get_data_from_db()
        self.__map_courses_to_units()
        self.__YOLO()
        self.__no_course_overlap()
        


def main():

    #TODO razdvojiti prve i druge vezbe(ako postoje)

    fg = FormulaGenerator("test_input.txt")

    num_of_results = 0
    unsat_count = 0
    fg.code()
    c = DimacsCoder(fg.formula)
    dimacs_string = c.create_dimacs_string()

    while True:
        if unsat_count > 1000 or num_of_results > 100:
            break
        dimacs_in = open("out.cnf", "w")
        dimacs_out = open("solution.cnf", "r")

        dimacs_in.writelines(dimacs_string)
        dimacs_in.flush()

        subprocess.run(["minisat", "out.cnf", "solution.cnf"])
        dimacs_in.close()

        is_solved = dimacs_out.readline().strip() == "SAT"
        if is_solved:
            solution = dimacs_out.readline()
            solution = solution.split(" ")
            solution = solution[:-1] #all but last 0
            res = c.decode_dimacs_string(solution)
            with open(f"output/result{num_of_results}.html", "w") as html_file:
                html_file.writelines(timetable_to_html(res) )

            num_of_results += 1

            #increase number of clauses
            tmp = dimacs_string.split("\n")
            num_of_clauses = int(tmp[0].split(" ")[-1]) + 1
            num_of_vars = int(tmp[0].split(" ")[2])
            dimacs_string = f"p cnf {num_of_vars} {num_of_clauses}\n" + "\n".join(tmp[1:])

            #we forbid current solution so we get other combinations
            tmp : str = ''
            for s in solution:
                if s[0] == '-':#if negated
                    tmp += s[1:] + ' '#then add positive
                else: #else add negated
                    tmp += '-' + s + ' '
            
            dimacs_string += tmp + '0\n'
        else:
            fg.remove_unit()
            fg.code()
            c = DimacsCoder(fg.formula)
            dimacs_string = c.create_dimacs_string()
            unsat_count += 1
            print("UNSAT")
        dimacs_out.close()

if __name__ == "__main__":
    main()
