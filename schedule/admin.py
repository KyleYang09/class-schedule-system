from django.contrib import admin

from .models import ClassGroup, Course, Period, Profile, Room, Slot, Teacher

admin.site.site_header = '課表維護系統'
admin.site.site_title = '課表維護系統'
admin.site.index_title = '資料管理'

admin.site.register([ClassGroup, Room, Period])


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


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_approved', 'created_by']
    list_filter = ['is_approved']
    list_select_related = ['created_by']
    search_fields = ['name']
    actions = ['approve']

    @admin.action(description='核准選取的教師')
    def approve(self, request, queryset):
        queryset.update(is_approved=True)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'class_group', 'teacher', 'created_at']
    list_filter = ['role', 'class_group']
    list_select_related = ['user', 'class_group', 'teacher']
    search_fields = ['user__email', 'user__username']
