import typing as ty
from .utils import lecture_enum

class timetable_unit:
    def __init__(self, day: int, start_time: int, finish_time: int, sub: str,
                 type: int, group: str, room: str, hash: str, **kwargs):
        self.day = day
        self.start_time = start_time
        self.finish_time = finish_time
        self.subject = sub
        self.type = type
        self.group = group
        self.room = room
        self.hash = hash
        self.teacher: ty.Optional[str] = kwargs.get('teacher')
        self.sub_group: ty.Optional[ty.List[str]] = kwargs.get('sub_group')

    def type_text(self)->str:
        if self.type == lecture_enum.LECTURE:
            type_name = 'Предавања'
        elif self.type == lecture_enum.PRACTICAL:
            type_name = 'Вежбе'
        else:
            type_name = 'Практикум'
        return type_name

    def teacher_safe(self)->str:
        return self.teacher if self.teacher is not None else ''

    def sub_group_safe(self)->ty.List[str]:
        return self.sub_group if self.sub_group is not None else []

    def __str__(self):
        return str(self.subject) + ' ' + str(self.type) + ' ' + str(self.group) +  ' (dan: ' + str(self.day) + ', start: ' + \
                str(self.start_time) + ', end: ' + str(self.finish_time) + ', room: ' + str(self.room)\
                +')'

    def __repr__(self):
        return self.__str__()
               
