from datetime import datetime, timedelta

from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import ClassGroup, Course, Period, Slot, Teacher, Weekday

TINT_COUNT = 4
WEEKDAY_LABELS = dict(Weekday.choices)
LUNCH_MARKER = (12, 30)


def _minutes_between(earlier, later):
    day = datetime(2000, 1, 1)
    return (datetime.combine(day, later) - datetime.combine(day, earlier)) / timedelta(minutes=1)


def build_grid(slots, detail):
    periods = list(Period.objects.all())
    days = [
        day for day in Weekday.values
        if day <= 5 or any(slot.weekday == day for slot in slots)
    ]
    cells = {(slot.weekday, slot.period_id): slot for slot in slots}
    rows = []
    previous = None
    for period in periods:
        break_label = ''
        if previous and _minutes_between(previous.end_time, period.start_time) >= 60:
            noon = previous.end_time.replace(hour=LUNCH_MARKER[0], minute=LUNCH_MARKER[1])
            break_label = '午休' if previous.end_time <= noon <= period.start_time else '休息'
        row_cells = []
        for day in days:
            slot = cells.get((day, period.id))
            row_cells.append(
                slot and {
                    'name': slot.course.name,
                    'detail': detail(slot),
                    'room': slot.room.name,
                    'tint': slot.course_id % TINT_COUNT,
                }
            )
        rows.append({
            'period': period,
            'break_label': break_label,
            'break_time': break_label and f'{previous.end_time:%H:%M}–{period.start_time:%H:%M}',
            'cells': row_cells,
        })
        previous = period
    return {
        'days': [{'number': day, 'label': WEEKDAY_LABELS[day]} for day in days],
        'rows': rows,
        'has_weekend': any(day > 5 for day in days),
    }


def _timetable_page(request, pk, queryset, field, detail, kind):
    items = list(queryset)
    if pk:
        current = next((item for item in items if item.pk == pk), None)
        if current is None:
            raise Http404
    else:
        current = items[0] if items else None
    context = {
        'kind': kind,
        'nav': kind,
        'items': items,
        'current': current,
        'today': timezone.localtime().isoweekday(),
    }
    if current:
        slots = list(
            Slot.objects.filter(**{field: current})
            .select_related('course', 'teacher', 'class_group', 'room', 'period')
        )
        context['grid'] = build_grid(slots, detail)
        context['lesson_count'] = len(slots)
        context['course_count'] = len({slot.course_id for slot in slots})
    return render(request, 'schedule/timetable.html', context)


def home(request):
    return redirect('class_index')


def class_timetable(request, pk=None):
    return _timetable_page(
        request, pk, ClassGroup.objects.all(), 'class_group',
        lambda slot: slot.teacher.name, 'class',
    )


def teacher_timetable(request, pk=None):
    return _timetable_page(
        request, pk, Teacher.objects.all(), 'teacher',
        lambda slot: slot.class_group.name, 'teacher',
    )


def my_timetable(request):
    courses = Course.objects.select_related('class_group', 'teacher').prefetch_related(
        'slots__room', 'slots__period'
    )
    data = {
        'periods': [
            {'id': p.id, 'code': p.code, 'start': f'{p.start_time:%H:%M}', 'end': f'{p.end_time:%H:%M}'}
            for p in Period.objects.all()
        ],
        'classes': [{'id': c.id, 'name': c.name} for c in ClassGroup.objects.all()],
        'weekdays': [{'number': n, 'label': label} for n, label in Weekday.choices],
        'courses': [
            {
                'id': course.id,
                'name': course.name,
                'classId': course.class_group_id,
                'className': course.class_group.name,
                'teacher': course.teacher.name,
                'slots': [
                    {'day': s.weekday, 'period': s.period_id, 'room': s.room.name}
                    for s in course.slots.all()
                ],
            }
            for course in courses
        ],
    }
    return render(request, 'schedule/my_timetable.html', {'data': data, 'nav': 'my'})

    
