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
from utils.html_writer import timetable_to_html
import typing as ty
import subprocess

def sqlite_connection_str(path: str)->str:
    """ :param path - absolute path to db or :memory: for in memory db"""
    return f'sqlite:///{path}'

class literal:
    def __init__(self, unit : timetable_unit, negated = False):
        self.unit : timetable_unit = unit
        self.negated = negated
        self.use = True
    def __str__(self):
        return ("NOT" if self.negated else 'YES') + str(self.unit)
    def __repr__(self):
        return self.__str__()

class disjunction:
    def __init__(self, literals : ty.List[literal]):
        self.literals = literals

class cnf_coded_formula:
    def __init__(self, formula : ty.List[disjunction]):
        self.formula : ty.List[disjunction] = formula
        self.num_of_clauses = 0

    def __create_cnf_mapping(self):
        self.cnf_course_maping = {}
        self.cnf_course_maping_inverse = {}
        i=1 #has to be 1 because 0 has predefined value
        for disjunction in self.formula:
            for literal in disjunction:
                #TODO ispitati zasto se ovo tacno desava
                if str(literal.unit) in self.cnf_course_maping:
                    continue
                self.cnf_course_maping[str(literal.unit)] = i
                self.cnf_course_maping_inverse[i] = literal.unit
                i+=1
        self.num_of_clauses = i-1
        #  print(self.cnf_course_maping)

    def create_cnf_str(self):
        self.__create_cnf_mapping()
        output_string : str = ''
        for disjunction in self.formula:
            for literal in disjunction:
                output_string += ('-' if literal.negated else '') + str(self.cnf_course_maping[str(literal.unit)]) + ' '
            output_string += '0\n'
        tmp = output_string.strip().split('\n')
        output_string = f'p cnf {self.num_of_clauses} {len(tmp)}' + '\n' + output_string
        #  print(output_string)
        return output_string

    def decode_from_cnf_str(self, solution: ty.List[int]):
        result : ty.List[timetable_unit] = []
        for s in solution:
            if s[0] != '-':
                result.append(self.cnf_course_maping_inverse[int(s)])
            #  else:
            #  result.append(self.cnf_course_maping_inverse[int(s)])
        return result        

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

    #TODO bolje ime
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
        self.removed_unit = self.all_timetable_units[0] #TODO test, ovo vraca PROIZVOLJAN element, ne svidja mi se bas
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

    unsat_count = 0
    while True:
        if unsat_count > 1000:
            break
        fg.code()
        c = cnf_coded_formula(fg.formula)
        cnf_string = c.create_cnf_str()

        with open("out.cnf", "w") as f:
            f.writelines(cnf_string)

        cnf_in = open("out.cnf", "r")
        cnf_out = open("solution.cnf", "w")
        subprocess.run(["minisat", "out.cnf", "solution.cnf"])
        with open("solution.cnf", "r") as f:
            solved = f.readline()
            if solved.strip() == "SAT":
                solution = f.readline()
                solution = solution.split(" ")
                solution = solution[:-1]
                res = c.decode_from_cnf_str(solution)
                #  print(res)
                with open("result.html", "w") as html_file:
                    html_file.writelines(timetable_to_html(res) )
                break
            else:
                unsat_count += 1
                fg.remove_unit()
                print("UNSAT")

if __name__ == "__main__":
    main()