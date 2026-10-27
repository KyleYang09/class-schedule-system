from datetime import datetime, timedelta

from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import ClassGroup, Course, Period, Slot, Teacher, Weekday

FILL_COUNT = 4
TILE_HEIGHT = 100
TILE_GAP = 8
CHAR_HEIGHT = 22
SMALL_CHAR_HEIGHT = 16
TILE_PADDING = 28
WEEKDAY_LABELS = dict(Weekday.choices)
LUNCH_MARKER = (12, 30)
BREAK_MINUTES = 60


def _minutes_between(earlier, later):
    day = datetime(2000, 1, 1)
    return (datetime.combine(day, later) - datetime.combine(day, earlier)) / timedelta(minutes=1)


def period_rows(now=None):
    rows = []
    previous = None
    for period in Period.objects.all():
        label = ''
        if previous and _minutes_between(previous.end_time, period.start_time) >= BREAK_MINUTES:
            noon = previous.end_time.replace(hour=LUNCH_MARKER[0], minute=LUNCH_MARKER[1])
            label = '午休' if previous.end_time <= noon <= period.start_time else '休息'
        rows.append({
            'period': period,
            'is_now': bool(now and period.start_time <= now <= period.end_time),
            'break_label': label,
            'break_time': label and f'{previous.end_time:%H:%M}–{period.start_time:%H:%M}',
        })
        previous = period
    return rows


def text_length(text, unit):
    return sum(unit * (0.55 if ord(char) < 128 else 1) for char in text)


def fits_vertically(cell):
    if cell['rowspan'] < 2:
        return False
    height = cell['rowspan'] * TILE_HEIGHT + (cell['rowspan'] - 1) * TILE_GAP - TILE_PADDING
    small = [cell['room'], *cell['details']]
    return (
        text_length(cell['name'], CHAR_HEIGHT) <= height
        and all(len(text) * SMALL_CHAR_HEIGHT <= height for text in small)
    )


def build_grid(slots, detail, today, now):
    rows = period_rows(now)
    days = list(Weekday.values)
    by_cell = {(slot.weekday, slot.period_id): slot for slot in slots}

    for index, row in enumerate(rows):
        row['cells'] = []
        for day in days:
            slot = by_cell.get((day, row['period'].id))
            above = rows[index - 1]['cells'][len(row['cells'])] if index else None
            if slot and above is not None and not row['break_label']:
                owner = above.get('merged_into') or above
                if owner.get('course_id') == slot.course_id and owner.get('room') == slot.room.name:
                    owner['rowspan'] += 1
                    row['cells'].append({'skip': True, 'merged_into': owner, 'course_id': slot.course_id})
                    continue
            row['cells'].append(
                {
                    'course_id': slot.course_id,
                    'name': slot.course.name,
                    'details': [detail(slot)],
                    'room': slot.room.name,
                    'fill': slot.course_id % FILL_COUNT,
                    'rowspan': 1,
                } if slot else {'empty': True, 'weekend': day > 5, 'today': day == today}
            )
    for row in rows:
        for cell in row['cells']:
            if 'name' in cell:
                cell['vertical'] = fits_vertically(cell)
    return {
        'days': [{'number': day, 'label': WEEKDAY_LABELS[day], 'weekend': day > 5} for day in days],
        'rows': rows,
        'has_weekend': any(slot.weekday > 5 for slot in slots),
    }


def _timetable_page(request, pk, queryset, field, detail, kind):
    local_now = timezone.localtime()
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
        'today': local_now.isoweekday(),
        'today_date': local_now.date(),
    }
    if current:
        slots = list(
            Slot.objects.filter(**{field: current})
            .select_related('course', 'teacher', 'class_group', 'room', 'period')
        )
        context['grid'] = build_grid(slots, detail, local_now.isoweekday(), local_now.time())
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
            {
                'id': row['period'].id,
                'code': row['period'].code,
                'start': f"{row['period'].start_time:%H:%M}",
                'end': f"{row['period'].end_time:%H:%M}",
                'breakLabel': row['break_label'],
                'breakTime': row['break_time'],
            }
            for row in period_rows()
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
    return render(
        request, 'schedule/my_timetable.html',
        {'data': data, 'nav': 'my', 'today_date': timezone.localtime().date()},
    )

def py_han(request):
    return render(request, "schedule/py_han.html", {"nav": "han"})
