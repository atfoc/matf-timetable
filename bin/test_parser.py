import logging
import typing as ty
from fileinput import filename

from parser.parser import parser
from parser.parser import lecture_enum



def callback(day:int, start: int, finish: int, sub: str, type: int, teacher: ty.Optional[str], group: str,
             sub_group: ty.Optional[ty.List[str]], room: str, hash: str)->None:

    if type == lecture_enum.LECTURE:
        type_name = 'Predavanje'
    elif type == lecture_enum.PRACTICAL:
        type_name = 'Vezbe'
    else:
        type_name = 'Praktikum'

    print(f'Day: {day}')
    print(f'Time: {start}-{finish}')
    print(f'Subject: {sub}')
    print(f'Type: {type_name}')
    print(f'Teacher: {teacher if teacher is not None else ""}')
    print(f'Group: {group}')
    print(f'Sub_group: {sub_group if sub_group is not None else ""}')
    print(f'Room : {room}')
    print(f'Hash: {hash}')
    print('------------------------------------------------------------------------------')


def main():
    logging.basicConfig(filename='parser.log', level=logging.DEBUG)

    p = parser('http://poincare.matf.bg.ac.rs/~kmiljan/raspored/sve/index.html', True)

    p.parse(callback)



if __name__ == '__main__':
    main()
