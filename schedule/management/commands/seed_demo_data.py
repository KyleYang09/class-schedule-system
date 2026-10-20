from datetime import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from schedule.models import ClassGroup, Course, Period, Room, Slot, Teacher

PERIODS = {
    '1': (time(8, 15), time(9, 5)),
    '2': (time(9, 10), time(10, 0)),
    '3': (time(10, 10), time(11, 0)),
    '4': (time(11, 10), time(12, 0)),
    '5': (time(13, 30), time(14, 20)),
    '6': (time(14, 25), time(15, 15)),
    '7': (time(15, 25), time(16, 15)),
    '8': (time(16, 20), time(17, 10)),
    '9': (time(17, 20), time(18, 10)),
}

TEACHERS = ['王志明', '李雅婷', '陳建宏', '林佳穎', '張偉倫', '黃淑芬', '吳宗翰', '劉怡君', '蔡明哲', '鄭心怡']

ROOMS = ['A101', 'A102', 'A201', 'A202', 'B101', 'B102', 'B201', 'C301']

COURSES = {
    '資工一甲': [('程式設計', 0), ('離散數學', 1), ('微積分', 2), ('計算機概論', 3), ('大學英文', 4)],
    '資工二甲': [('資料結構', 0), ('線性代數', 2), ('數位邏輯', 5), ('物件導向程式設計', 1), ('大學英文', 4)],
    '電機一甲': [('電路學', 5), ('微積分', 2), ('普通物理', 6), ('程式設計', 0), ('大學英文', 4)],
    '電機二甲': [('電子學', 5), ('訊號與系統', 7), ('工程數學', 2), ('電磁學', 6), ('大學英文', 4)],
    '企管一甲': [('經濟學', 8), ('會計學', 9), ('管理學', 8), ('統計學', 3), ('大學英文', 4)],
    '企管二甲': [('行銷管理', 8), ('財務管理', 9), ('組織行為', 8), ('管理統計', 3), ('大學英文', 4)],
}

SATURDAY_EXTRA = [('企管二甲', '財務管理', 6, '2', 'B201')]

SLOTS_PER_COURSE = 2
WEEKDAYS = [1, 2, 3, 4, 5]
DEMO_USERNAME = 'admin'
DEMO_PASSWORD = 'demo1234'


class Command(BaseCommand):
    help = '建立節次與示範用課表資料,可重複執行'

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('示範資料只能在開發環境(DEBUG=1)建立')

        periods = {
            code: Period.objects.update_or_create(
                code=code, defaults={'start_time': start, 'end_time': end}
            )[0]
            for code, (start, end) in PERIODS.items()
        }
        teachers = [Teacher.objects.get_or_create(name=name)[0] for name in TEACHERS]
        rooms = {name: Room.objects.get_or_create(name=name)[0] for name in ROOMS}

        busy = {
            key: set(Slot.objects.values_list(key, 'weekday', 'period_id'))
            for key in ('class_group_id', 'teacher_id', 'room_id')
        }

        for offset, (class_name, courses) in enumerate(COURSES.items()):
            class_group = ClassGroup.objects.get_or_create(name=class_name)[0]
            for course_name, teacher_index in courses:
                course, _ = Course.objects.get_or_create(
                    class_group=class_group,
                    name=course_name,
                    defaults={'teacher': teachers[teacher_index]},
                )
                if course.slots.exists():
                    continue
                days = WEEKDAYS[offset % 5:] + WEEKDAYS[:offset % 5]
                used_days = set()
                for _ in range(SLOTS_PER_COURSE):
                    slot_key = next(
                        (day, period, room)
                        for day in days
                        if day not in used_days
                        for period in periods.values()
                        for room in rooms.values()
                        if (class_group.id, day, period.id) not in busy['class_group_id']
                        and (course.teacher_id, day, period.id) not in busy['teacher_id']
                        and (room.id, day, period.id) not in busy['room_id']
                    )
                    day, period, room = slot_key
                    Slot.objects.create(course=course, weekday=day, period=period, room=room)
                    busy['class_group_id'].add((class_group.id, day, period.id))
                    busy['teacher_id'].add((course.teacher_id, day, period.id))
                    busy['room_id'].add((room.id, day, period.id))
                    used_days.add(day)

        for class_name, course_name, day, period_code, room_name in SATURDAY_EXTRA:
            course = Course.objects.get(class_group__name=class_name, name=course_name)
            Slot.objects.get_or_create(
                course=course,
                weekday=day,
                period=periods[period_code],
                defaults={'room': rooms[room_name]},
            )

        User = get_user_model()
        if not User.objects.filter(username=DEMO_USERNAME).exists():
            User.objects.create_superuser(DEMO_USERNAME, password=DEMO_PASSWORD)

        self.stdout.write(self.style.SUCCESS(
            f'完成:{ClassGroup.objects.count()} 個班級、{Teacher.objects.count()} 位教師、'
            f'{Course.objects.count()} 門課程、{Slot.objects.count()} 個上課時段'
        ))
