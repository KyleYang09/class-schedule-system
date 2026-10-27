from datetime import time
from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .models import ClassGroup, Course, Period, Room, Slot, Teacher
from .views import build_grid, fits_vertically, period_rows, text_length


class ScheduleData(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.p1 = Period.objects.create(code='1', start_time=time(8, 15), end_time=time(9, 5))
        cls.p2 = Period.objects.create(code='2', start_time=time(9, 10), end_time=time(10, 0))
        cls.p3 = Period.objects.create(code='3', start_time=time(10, 10), end_time=time(11, 0))
        cls.p5 = Period.objects.create(code='5', start_time=time(13, 30), end_time=time(14, 20))
        cls.p6 = Period.objects.create(code='6', start_time=time(14, 25), end_time=time(15, 15))
        cls.class_a = ClassGroup.objects.create(name='資工一甲')
        cls.class_b = ClassGroup.objects.create(name='資工二甲')
        cls.teacher_a = Teacher.objects.create(name='王志明')
        cls.teacher_b = Teacher.objects.create(name='李雅婷')
        cls.room_a = Room.objects.create(name='A101')
        cls.room_b = Room.objects.create(name='A102')
        cls.course = Course.objects.create(class_group=cls.class_a, name='程式設計', teacher=cls.teacher_a)
        cls.other = Course.objects.create(class_group=cls.class_b, name='資料結構', teacher=cls.teacher_b)

    def slot(self, course, weekday, period, room=None):
        return Slot.objects.create(
            course=course, weekday=weekday, period=period, room=room or self.room_a
        )


class SlotConstraintTests(ScheduleData):
    def assertRejected(self, **kwargs):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.slot(**kwargs)

    def test_slot_copies_class_and_teacher_from_course(self):
        slot = self.slot(self.course, 1, self.p1)
        self.assertEqual(slot.class_group, self.class_a)
        self.assertEqual(slot.teacher, self.teacher_a)

    def test_same_class_cannot_have_two_courses_at_same_time(self):
        second = Course.objects.create(class_group=self.class_a, name='離散數學', teacher=self.teacher_b)
        self.slot(self.course, 1, self.p1)
        self.assertRejected(course=second, weekday=1, period=self.p1, room=self.room_b)

    def test_same_teacher_cannot_teach_two_classes_at_same_time(self):
        second = Course.objects.create(class_group=self.class_b, name='微積分', teacher=self.teacher_a)
        self.slot(self.course, 1, self.p1)
        self.assertRejected(course=second, weekday=1, period=self.p1, room=self.room_b)

    def test_same_room_cannot_be_used_twice_at_same_time(self):
        self.slot(self.course, 1, self.p1, self.room_a)
        self.assertRejected(course=self.other, weekday=1, period=self.p1, room=self.room_a)

    def test_same_period_on_different_days_is_allowed(self):
        self.slot(self.course, 1, self.p1)
        self.slot(self.course, 2, self.p1)
        self.assertEqual(Slot.objects.count(), 2)

    def test_weekday_must_be_between_one_and_seven(self):
        for weekday in (0, 8):
            with self.assertRaises(IntegrityError), transaction.atomic():
                self.slot(self.course, weekday, self.p1)

    def test_validation_reports_conflict_message_for_forms(self):
        self.slot(self.course, 1, self.p1, self.room_a)
        clash = Slot(course=self.other, weekday=1, period=self.p1, room=self.room_a)
        with self.assertRaises(ValidationError) as caught:
            clash.validate_constraints()
        self.assertIn('該教室在這個時段已被使用', str(caught.exception))

    def test_changing_course_teacher_updates_its_slots(self):
        slot = self.slot(self.course, 1, self.p1)
        self.course.teacher = self.teacher_b
        self.course.save()
        slot.refresh_from_db()
        self.assertEqual(slot.teacher, self.teacher_b)

    def test_moving_course_to_busy_teacher_time_fails_validation(self):
        self.slot(self.course, 1, self.p1, self.room_a)
        self.slot(self.other, 1, self.p1, self.room_b)
        self.course.teacher = self.teacher_b
        with self.assertRaises(ValidationError):
            self.course.clean()


class OtherModelConstraintTests(ScheduleData):
    def test_period_end_must_be_after_start(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Period.objects.create(code='9', start_time=time(10, 0), end_time=time(10, 0))

    def test_course_name_is_unique_within_a_class(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Course.objects.create(class_group=self.class_a, name='程式設計', teacher=self.teacher_b)

    def test_same_course_name_is_allowed_in_different_classes(self):
        Course.objects.create(class_group=self.class_b, name='程式設計', teacher=self.teacher_b)
        self.assertEqual(Course.objects.filter(name='程式設計').count(), 2)

    def test_periods_are_ordered_by_start_time(self):
        codes = list(Period.objects.values_list('code', flat=True))
        self.assertEqual(codes, ['1', '2', '3', '5', '6'])


class PeriodRowsTests(ScheduleData):
    def test_no_break_label_between_consecutive_periods(self):
        rows = period_rows()
        self.assertEqual([row['break_label'] for row in rows[:3]], ['', '', ''])

    def test_lunch_label_when_gap_covers_noon(self):
        row = next(row for row in period_rows() if row['period'].code == '5')
        self.assertEqual(row['break_label'], '午休')
        self.assertEqual(row['break_time'], '11:00–13:30')

    def test_generic_break_label_when_gap_misses_noon(self):
        Period.objects.create(code='8', start_time=time(17, 20), end_time=time(18, 10))
        row = next(row for row in period_rows() if row['period'].code == '8')
        self.assertEqual(row['break_label'], '休息')

    def test_current_period_is_marked(self):
        rows = period_rows(now=time(9, 30))
        self.assertEqual([row['period'].code for row in rows if row['is_now']], ['2'])

    def test_no_period_is_current_during_lunch(self):
        rows = period_rows(now=time(12, 30))
        self.assertFalse(any(row['is_now'] for row in rows))


class BuildGridTests(ScheduleData):
    def grid(self, today=1, now=time(8, 30)):
        slots = Slot.objects.select_related('course', 'teacher', 'class_group', 'room', 'period')
        return build_grid(list(slots), lambda s: s.teacher.name, today, now)

    def cells(self, grid, code):
        return next(row for row in grid['rows'] if row['period'].code == code)['cells']

    def test_always_shows_seven_days(self):
        grid = self.grid()
        self.assertEqual(len(grid['days']), 7)
        self.assertEqual([d['weekend'] for d in grid['days']], [False] * 5 + [True] * 2)
        for row in grid['rows']:
            self.assertEqual(len(row['cells']), 7)

    def test_has_weekend_only_when_weekend_slot_exists(self):
        self.slot(self.course, 1, self.p1)
        self.assertFalse(self.grid()['has_weekend'])
        self.slot(self.course, 6, self.p2)
        self.assertTrue(self.grid()['has_weekend'])

    def test_empty_cells_know_weekend_and_today(self):
        cells = self.cells(self.grid(today=3), '1')
        self.assertTrue(cells[2]['today'])
        self.assertFalse(cells[0]['today'])
        self.assertTrue(cells[5]['weekend'])

    def test_slot_cell_carries_course_details(self):
        self.slot(self.course, 2, self.p1)
        cell = self.cells(self.grid(), '1')[1]
        self.assertEqual(cell['name'], '程式設計')
        self.assertEqual(cell['room'], 'A101')
        self.assertEqual(cell['details'], ['王志明'])
        self.assertEqual(cell['rowspan'], 1)

    def test_consecutive_periods_of_same_course_and_room_merge(self):
        self.slot(self.course, 1, self.p1)
        self.slot(self.course, 1, self.p2)
        self.slot(self.course, 1, self.p3)
        first = self.cells(self.grid(), '1')[0]
        self.assertEqual(first['rowspan'], 3)
        self.assertTrue(self.cells(self.grid(), '2')[0]['skip'])
        self.assertTrue(self.cells(self.grid(), '3')[0]['skip'])

    def test_different_room_does_not_merge(self):
        self.slot(self.course, 1, self.p1, self.room_a)
        self.slot(self.course, 1, self.p2, self.room_b)
        grid = self.grid()
        self.assertEqual(self.cells(grid, '1')[0]['rowspan'], 1)
        self.assertNotIn('skip', self.cells(grid, '2')[0])

    def test_different_course_does_not_merge(self):
        second = Course.objects.create(class_group=self.class_a, name='離散數學', teacher=self.teacher_b)
        self.slot(self.course, 1, self.p1)
        self.slot(second, 1, self.p2)
        self.assertEqual(self.cells(self.grid(), '1')[0]['rowspan'], 1)

    def test_lunch_break_stops_merging(self):
        self.slot(self.course, 1, self.p3)
        self.slot(self.course, 1, self.p5)
        grid = self.grid()
        self.assertEqual(self.cells(grid, '3')[0]['rowspan'], 1)
        self.assertNotIn('skip', self.cells(grid, '5')[0])

    def test_merging_is_per_day(self):
        self.slot(self.course, 1, self.p1)
        self.slot(self.course, 2, self.p2)
        grid = self.grid()
        self.assertEqual(self.cells(grid, '1')[0]['rowspan'], 1)
        self.assertNotIn('skip', self.cells(grid, '2')[1])

    def test_current_period_flag_is_set_on_the_row(self):
        grid = self.grid(now=time(9, 30))
        self.assertEqual([r['period'].code for r in grid['rows'] if r['is_now']], ['2'])


class TextLayoutTests(SimpleTestCase):
    def test_ascii_characters_are_narrower_than_cjk(self):
        self.assertLess(text_length('ABCD', 20), text_length('資料結構', 20))

    def test_single_row_tile_is_never_vertical(self):
        cell = {'rowspan': 1, 'name': '程式', 'room': 'A101', 'details': ['王志明']}
        self.assertFalse(fits_vertically(cell))

    def test_tall_tile_with_short_text_is_vertical(self):
        cell = {'rowspan': 3, 'name': '程式設計', 'room': 'A101', 'details': ['王志明']}
        self.assertTrue(fits_vertically(cell))

    def test_long_name_does_not_fit_vertically(self):
        cell = {'rowspan': 2, 'name': '物件導向程式設計與實習', 'room': 'A101', 'details': ['王志明']}
        self.assertFalse(fits_vertically(cell))


class PageTests(ScheduleData):
    def setUp(self):
        self.slot(self.course, 1, self.p1)
        self.slot(self.other, 2, self.p2, self.room_b)

    def test_home_is_my_timetable(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'schedule/my_timetable.html')

    def test_old_my_url_redirects_to_home(self):
        response = self.client.get('/my/')
        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_list_pages_return_200(self):
        for name in ('class_index', 'teacher_index', 'py_han'):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_class_index_shows_first_class_timetable(self):
        response = self.client.get(reverse('class_index'))
        self.assertEqual(response.context['current'], self.class_a)
        self.assertContains(response, '程式設計')

    def test_class_page_shows_only_that_classes_courses(self):
        response = self.client.get(reverse('class_timetable', args=[self.class_a.pk]))
        self.assertContains(response, '程式設計')
        self.assertNotContains(response, '資料結構')

    def test_class_page_summary_counts(self):
        response = self.client.get(reverse('class_timetable', args=[self.class_a.pk]))
        self.assertEqual(response.context['lesson_count'], 1)
        self.assertEqual(response.context['course_count'], 1)

    def test_teacher_page_shows_class_name_as_detail(self):
        response = self.client.get(reverse('teacher_timetable', args=[self.teacher_a.pk]))
        self.assertContains(response, '資工一甲')

    def test_unknown_class_and_teacher_return_404(self):
        for name in ('class_timetable', 'teacher_timetable'):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name, args=[99999])).status_code, 404)

    def test_unknown_url_returns_404(self):
        self.assertEqual(self.client.get('/no-such-page/').status_code, 404)

    def test_my_timetable_exposes_all_courses_to_the_script(self):
        response = self.client.get('/')
        names = {course['name'] for course in response.context['data']['courses']}
        self.assertEqual(names, {'程式設計', '資料結構'})

    def test_my_timetable_course_lists_its_slots(self):
        response = self.client.get('/')
        course = next(c for c in response.context['data']['courses'] if c['name'] == '程式設計')
        self.assertEqual(
            course['slots'], [{'day': 1, 'period': self.p1.id, 'room': 'A101'}]
        )

    def test_my_timetable_exposes_period_times(self):
        response = self.client.get('/')
        first = response.context['data']['periods'][0]
        self.assertEqual((first['start'], first['end']), ('08:15', '09:05'))

    def test_navigation_marks_current_page(self):
        response = self.client.get(reverse('class_index'))
        self.assertContains(response, '<a href="/classes/" aria-current="page">')
        self.assertNotContains(response, '<a href="/" aria-current="page">')

    def test_nav_links_point_to_expected_urls(self):
        response = self.client.get('/')
        for name in ('my_timetable', 'class_index', 'teacher_index'):
            self.assertContains(response, f'href="{reverse(name)}"')


class EmptyDatabaseTests(TestCase):
    def test_pages_do_not_crash_without_data(self):
        for url in ('/', '/classes/', '/teachers/'):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)


@override_settings(DEBUG=True)
class SeedCommandTests(TestCase):
    def run_seed(self):
        call_command('seed_demo_data', stdout=StringIO())

    def test_creates_demo_data(self):
        self.run_seed()
        self.assertEqual(ClassGroup.objects.count(), 6)
        self.assertEqual(Teacher.objects.count(), 10)
        self.assertEqual(Course.objects.count(), 30)
        self.assertTrue(Period.objects.filter(code='1', start_time=time(8, 15)).exists())

    def test_can_be_run_twice_without_duplicates(self):
        self.run_seed()
        counts = (Course.objects.count(), Slot.objects.count(), Period.objects.count())
        self.run_seed()
        self.assertEqual(counts, (Course.objects.count(), Slot.objects.count(), Period.objects.count()))

    def test_every_course_has_at_least_one_slot(self):
        self.run_seed()
        self.assertFalse(Course.objects.filter(slots__isnull=True).exists())

    def test_seeded_data_has_a_weekend_class(self):
        self.run_seed()
        self.assertTrue(Slot.objects.filter(weekday__gte=6).exists())

    @override_settings(DEBUG=False)
    def test_refuses_to_run_outside_debug(self):
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            self.run_seed()
