import logging
import typing as ty
import os
from dashtable import data2rst
from timetable_parser.parser import parser
from timetable_parser.timetable_unit import timetable_unit




class callback:
    def __init__(self, dir_name: str):
        self.table = None
        self.group = ''
        self.dir_name = dir_name

        self.reset()


    def __call__(self, unit: timetable_unit)->None:


        if self.group == '':
            self.group = unit.group
        if self.group != unit.group:
            self.print()
            self.group = unit.group
            self.reset()

        if self.table[unit.day+1][unit.start_time-7] == '':
            self.table[unit.day+1][unit.start_time-7] = unit.subject+ '\n' + unit.sub_group_safe()
        else:
            if isinstance(self.table[unit.day+1][unit.start_time-7], list):
                self.table[unit.day+1][unit.start_time-7].append([unit.subject+ '\n' + unit.teacher_safe()])
            else:
                self.table[unit.day+1][unit.start_time-7] = [[self.table[unit.day+1][unit.start_time-7]], [unit.subject + '\n' + unit.teacher_safe()]]
        if unit.start_time != unit.finish_time-1:
            self.span.append([[unit.day+1, i] for i in range(unit.start_time-7, unit.finish_time-7)])



    def print(self):

        if not os.path.exists(os.path.join('.', self.dir_name)):
            os.mkdir(os.path.join('.', self.dir_name))

        for i in range(len(self.table)):
            for j in range(len(self.table[i])):
                if isinstance(self.table[i][j], list):
                    self.table[i][j] = data2rst(self.table[i][j], center_cells=True, use_headers=False)

        with open(os.path.join('.', self.dir_name, f'{self.group}.txt'), 'w') as f:
            f.write(data2rst(self.table, self.span, center_cells=True))

    def reset(self):
        self.table = [list(['' for i in range(14)]) for i in range(6)]
        self.span = []
        for i in range(13):
            self.table[0][i+1] = str(8+i) + '-' + str(8+i+1)

        self.table[1][0] = 'Ponedeljak'
        self.table[2][0] = 'Utorak'
        self.table[3][0] = 'Sreda'
        self.table[4][0] = 'Cetvrtak'
        self.table[5][0] = 'Petak'


def main():
    logging.basicConfig(filename='timetable_parser.log', level=logging.DEBUG)

    p = parser('http://poincare.matf.bg.ac.rs/~kmiljan/raspored/sve/index.html', True)

    c = callback('raspored')

    p.parse(c)

    c.print()





if __name__ == '__main__':
    main()