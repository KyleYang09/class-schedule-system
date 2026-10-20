from django.contrib import admin

from .models import ClassGroup, Course, Period, Room, Slot, Teacher

admin.site.register([ClassGroup, Teacher, Room, Period])


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'class_group', 'teacher']
    list_filter = ['class_group', 'teacher']
    list_select_related = ['class_group', 'teacher']
    search_fields = ['name']


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ['class_group', 'weekday', 'period', 'course', 'teacher', 'room']
    list_filter = ['class_group', 'teacher', 'room', 'weekday']
    list_select_related = ['class_group', 'teacher', 'room', 'period', 'course']
