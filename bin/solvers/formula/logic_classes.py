import typing as ty
from timetable_parser.timetable_unit import timetable_unit

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
