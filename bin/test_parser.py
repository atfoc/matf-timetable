import logging
import typing as ty

from parser.parser import parser
from parser.timetable_unit import timetable_unit



def callback(unit: timetable_unit)->None:


    print(f'Day: {unit.day}')
    print(f'Time: {unit.start_time}-{unit.finish_time}')
    print(f'Subject: {unit.subject}')
    print(f'Type: {unit.type_text()}')
    print(f'Teacher: {unit.teacher_safe()}')
    print(f'Group: {unit.group}')
    print(f'Sub_group: {unit.sub_group_safe()}')
    print(f'Room : {unit.room}')
    print(f'Hash: {unit.hash}')
    print('------------------------------------------------------------------------------')


def main():
    logging.basicConfig(filename='parser.log', level=logging.DEBUG)

    p = parser('http://poincare.matf.bg.ac.rs/~kmiljan/raspored/sve/index.html', True)

    p.parse(callback)



if __name__ == '__main__':
    main()
