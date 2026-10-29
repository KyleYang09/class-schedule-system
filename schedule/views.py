from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import OnboardingForm
from .models import ClassGroup, Course, CourseOverride, Period, Profile, Slot, Teacher, Weekday

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
                    row['cells'].append({
                        'skip': True,
                        'merged_into': owner,
                        'course_id': slot.course_id,
                        'name': slot.course.name,
                        'details': [detail(slot)],
                        'room': slot.room.name,
                    })
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
        'days': [
            {
                'number': day,
                'label': WEEKDAY_LABELS[day],
                'weekend': day > 5,
                'has_lessons': any(slot.weekday == day for slot in slots),
                'lesson_count': sum(slot.weekday == day for slot in slots),
            }
            for day in days
        ],
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


def class_timetable(request, pk=None):
    return _timetable_page(
        request, pk, ClassGroup.objects.all(), 'class_group',
        lambda slot: slot.teacher.name, 'class',
    )


def teacher_timetable(request, pk=None):
    return _timetable_page(
        request, pk, Teacher.objects.filter(is_approved=True), 'teacher',
        lambda slot: slot.class_group.name, 'teacher',
    )


def _course_override_state(user, profile):
    base_courses = Course.objects.filter(class_group=profile.class_group) if profile.class_group_id else Course.objects.none()
    base_ids = set(base_courses.values_list('id', flat=True))
    required_ids = set(base_courses.filter(is_required=True).values_list('id', flat=True))
    overrides = {
        override.course_id: override.action
        for override in CourseOverride.objects.filter(user=user)
    }
    selected_ids = (base_ids - {
        course_id for course_id, action in overrides.items()
        if action == CourseOverride.Action.DROP
    }) | {
        course_id for course_id, action in overrides.items()
        if action == CourseOverride.Action.ADD
    } | required_ids
    return base_ids, required_ids, selected_ids, overrides


@login_required
def my_timetable(request):
    if request.user.is_staff:
        return redirect('class_index')
    profile = Profile.objects.select_related('class_group', 'teacher').filter(user=request.user).first()
    if profile is None:
        return redirect('onboarding')
    if profile.role == Profile.Role.TEACHER:
        return redirect('teacher_timetable', pk=profile.teacher_id)

    _, required_ids, selected_ids, _ = _course_override_state(request.user, profile)
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
                'isRequired': course.is_required,
                'slots': [
                    {'day': s.weekday, 'period': s.period_id, 'room': s.room.name}
                    for s in course.slots.all()
                ],
            }
            for course in courses
        ],
        'selectedIds': sorted(selected_ids),
        'requiredIds': sorted(required_ids),
        'defaultClassId': profile.class_group_id,
    }
    return render(
        request, 'schedule/my_timetable.html',
        {
            'data': data,
            'nav': 'my',
            'today_date': timezone.localtime().date(),
            'save_url': 'update_my_timetable',
        },
    )


@login_required
def update_my_timetable(request):
    if request.method != 'POST':
        return JsonResponse({'error': '請使用 POST 儲存課表。'}, status=405)
    profile = Profile.objects.select_related('class_group').filter(
        user=request.user, role=Profile.Role.STUDENT
    ).first()
    if profile is None:
        return JsonResponse({'error': '請先完成學生身分設定。'}, status=403)

    try:
        requested_ids = {int(value) for value in request.POST.getlist('course_ids')}
    except (TypeError, ValueError):
        return JsonResponse({'error': '課程資料無效，請重新整理後再試。'}, status=400)

    courses = Course.objects.filter(pk__in=requested_ids)
    if courses.count() != len(requested_ids):
        return JsonResponse({'error': '部分課程已不存在，請重新整理課表。'}, status=400)

    base_courses = Course.objects.filter(class_group=profile.class_group) if profile.class_group_id else Course.objects.none()
    base_ids = set(base_courses.values_list('id', flat=True))
    required_ids = set(base_courses.filter(is_required=True).values_list('id', flat=True))
    missing_required = required_ids - requested_ids
    if missing_required:
        return JsonResponse({'error': '必修課程不可退選，請保留所有必修課程。'}, status=400)

    overlaps = {}
    slots = Slot.objects.filter(course_id__in=requested_ids).select_related(
        'course', 'period'
    )
    for slot in slots:
        key = (slot.weekday, slot.period_id)
        overlaps.setdefault(key, []).append(slot)
    conflicts = [
        {
            'day': Weekday(key[0]).label,
            'period': slots_in_cell[0].period.code,
            'courses': [slot.course.name for slot in slots_in_cell],
        }
        for key, slots_in_cell in overlaps.items()
        if len(slots_in_cell) > 1
    ]
    if conflicts:
        return JsonResponse({
            'error': '課表有時段衝突，請調整選課後再儲存。',
            'conflicts': conflicts,
        }, status=409)

    current_overrides = {
        override.course_id: override
        for override in CourseOverride.objects.filter(user=request.user)
    }
    all_relevant_ids = base_ids | requested_ids | set(current_overrides)
    with transaction.atomic():
        for course_id in all_relevant_ids:
            is_default = course_id in base_ids
            is_selected = course_id in requested_ids or course_id in required_ids
            if is_default == is_selected:
                CourseOverride.objects.filter(user=request.user, course_id=course_id).delete()
                continue
            action = CourseOverride.Action.ADD if is_selected else CourseOverride.Action.DROP
            CourseOverride.objects.update_or_create(
                user=request.user,
                course_id=course_id,
                defaults={'action': action},
            )

    return JsonResponse({'ok': True, 'selectedIds': sorted(requested_ids)})

@login_required
def onboarding(request):
    if request.user.is_staff or Profile.objects.filter(user=request.user).exists():
        return redirect('my_timetable')
    form = OnboardingForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        try:
            form.save(request.user)
        except IntegrityError:
            if Profile.objects.filter(user=request.user).exists():
                return redirect('my_timetable')
            form.add_error(None, '儲存時發生衝突，請再試一次')
        else:
            return redirect('my_timetable')
    return render(request, 'schedule/onboarding.html', {'form': form})


def py_han(request):
    return render(request, "schedule/py_han.html", {"nav": "han"})

def py_hsin(request):
    return render(request, "schedule/py_hsin.html", {"nav": "hsin"})

def py_hy(request):
    return render(request, "schedule/py_hy.html", {"nav": "hy"})

def py_jai_chen(request):
    return render(request, "schedule/py_jai_chen.html", {"nav": "jai_chen"})
