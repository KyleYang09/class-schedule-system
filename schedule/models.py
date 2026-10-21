from django.db import models


class Weekday(models.IntegerChoices):
    MONDAY = 1, '週一'
    TUESDAY = 2, '週二'
    WEDNESDAY = 3, '週三'
    THURSDAY = 4, '週四'
    FRIDAY = 5, '週五'
    SATURDAY = 6, '週六'
    SUNDAY = 7, '週日'


class ClassGroup(models.Model):
    name = models.CharField('班級', max_length=50, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = verbose_name_plural = '班級'

    def __str__(self):
        return self.name


class Teacher(models.Model):
    name = models.CharField('教師', max_length=50, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = verbose_name_plural = '教師'

    def __str__(self):
        return self.name


class Room(models.Model):
    name = models.CharField('教室', max_length=50, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = verbose_name_plural = '教室'

    def __str__(self):
        return self.name


class Period(models.Model):
    code = models.CharField('節次', max_length=2, unique=True)
    start_time = models.TimeField('開始時間')
    end_time = models.TimeField('結束時間')

    class Meta:
        ordering = ['start_time']
        verbose_name = verbose_name_plural = '節次'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F('start_time')),
                name='period_end_after_start',
                violation_error_message='結束時間必須晚於開始時間',
            ),
        ]

    def __str__(self):
        return f'第 {self.code} 節 {self.start_time:%H:%M}–{self.end_time:%H:%M}'


class Course(models.Model):
    class_group = models.ForeignKey(
        ClassGroup, on_delete=models.PROTECT, related_name='courses', verbose_name='班級'
    )
    name = models.CharField('課程名稱', max_length=100)
    teacher = models.ForeignKey(
        Teacher, on_delete=models.PROTECT, related_name='courses', verbose_name='授課教師'
    )

    class Meta:
        ordering = ['class_group__name', 'name']
        verbose_name = verbose_name_plural = '課程'
        constraints = [
            models.UniqueConstraint(
                fields=['class_group', 'name'],
                name='course_unique_per_class',
                violation_error_message='該班級已有同名課程',
            ),
        ]

    def __str__(self):
        return f'{self.class_group}　{self.name}'

    def clean(self):
        if self.pk and self.class_group_id and self.teacher_id:
            for slot in self.slots.all():
                slot.course = self
                slot.validate_constraints()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.slots.update(class_group_id=self.class_group_id, teacher_id=self.teacher_id)


class Slot(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='slots', verbose_name='課程'
    )
    weekday = models.PositiveSmallIntegerField('星期', choices=Weekday)
    period = models.ForeignKey(
        Period, on_delete=models.PROTECT, related_name='slots', verbose_name='節次'
    )
    room = models.ForeignKey(
        Room, on_delete=models.PROTECT, related_name='slots', verbose_name='教室'
    )
    class_group = models.ForeignKey(
        ClassGroup, on_delete=models.PROTECT, related_name='slots', editable=False, verbose_name='班級'
    )
    teacher = models.ForeignKey(
        Teacher, on_delete=models.PROTECT, related_name='slots', editable=False, verbose_name='教師'
    )

    class Meta:
        ordering = ['weekday', 'period__start_time']
        verbose_name = verbose_name_plural = '上課時段'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(weekday__gte=1, weekday__lte=7),
                name='slot_weekday_range',
            ),
            models.UniqueConstraint(
                fields=['class_group', 'weekday', 'period'],
                name='slot_unique_class_time',
                violation_error_message='該班級在這個時段已有其他課程',
            ),
            models.UniqueConstraint(
                fields=['teacher', 'weekday', 'period'],
                name='slot_unique_teacher_time',
                violation_error_message='該教師在這個時段已有其他課程',
            ),
            models.UniqueConstraint(
                fields=['room', 'weekday', 'period'],
                name='slot_unique_room_time',
                violation_error_message='該教室在這個時段已被使用',
            ),
        ]

    def __str__(self):
        return f'{self.course}　{self.get_weekday_display()} {self.period}'

    def sync_owner(self):
        self.class_group_id = self.course.class_group_id
        self.teacher_id = self.course.teacher_id

    def validate_constraints(self, exclude=None):
        if self.course_id:
            self.sync_owner()
            exclude = set(exclude or ()) - {'class_group', 'teacher'}
        super().validate_constraints(exclude)

    def save(self, *args, **kwargs):
        self.sync_owner()
        super().save(*args, **kwargs)
