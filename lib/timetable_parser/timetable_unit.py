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
            type_name = 'Predavanje'
        elif self.type == lecture_enum.PRACTICAL:
            type_name = 'Vezbe'
        else:
            type_name = 'Praktikum'


        return type_name

    def teacher_safe(self)->str:
        return self.teacher if self.teacher is not None else ''

    def sub_group_safe(self)->ty.List[str]:
        return self.sub_group if self.sub_group is not None else []
