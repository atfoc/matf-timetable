import typing as ty
from timetable_parser.timetable_unit import timetable_unit
from logic_classes import literal, disjunction

class DimacsCoder:
    def __init__(self, formula : ty.List[disjunction]):
        self.formula : ty.List[disjunction] = formula
        self.num_of_clauses = 0

    def __create_dimacs_maping(self):
        self.dimacs_course_maping = {}
        self.dimacs_course_maping_inverse = {}
        i=1 #has to be 1 because 0 has predefined value
        for disjunction in self.formula:
            for literal in disjunction:
                #TODO ispitati zasto se ovo tacno desava
                if str(literal.unit) in self.dimacs_course_maping:
                    continue
                self.dimacs_course_maping[str(literal.unit)] = i
                self.dimacs_course_maping_inverse[i] = literal.unit
                i+=1
        self.num_of_clauses = i-1
        #  print(self.dimacs_course_maping)

    def create_dimacs_string(self):
        self.__create_dimacs_maping()
        output_string : str = ''
        for disjunction in self.formula:
            for literal in disjunction:
                output_string += ('-' if literal.negated else '') + str(self.dimacs_course_maping[str(literal.unit)]) + ' '
            output_string += '0\n'
        tmp = output_string.strip().split('\n')
        output_string = f'p cnf {self.num_of_clauses} {len(tmp)}' + '\n' + output_string
        #  print(output_string)
        return output_string

    def decode_dimacs_string(self, solution: ty.List[int]):
        result : ty.List[timetable_unit] = []
        for s in solution:
            if s[0] != '-':
                result.append(self.dimacs_course_maping_inverse[int(s)])
            #  else:
            #  result.append(self.dimacs_course_maping_inverse[int(s)])
        return result 
