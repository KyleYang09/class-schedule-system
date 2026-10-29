from django.contrib import admin

from .models import ClassGroup, Course, CourseOverride, Period, Profile, Room, Slot, Teacher

admin.site.site_header = '課表維護系統'
admin.site.site_title = '課表維護系統'
admin.site.index_title = '資料管理'

admin.site.register([ClassGroup, Room, Period])


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'class_group', 'teacher', 'is_required']
    list_filter = ['class_group', 'teacher', 'is_required']
    list_editable = ['is_required']
    list_select_related = ['class_group', 'teacher']
    search_fields = ['name']


@admin.register(CourseOverride)
class CourseOverrideAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'action', 'updated_at']
    list_filter = ['action', 'course__class_group']
    list_select_related = ['user', 'course', 'course__class_group']
    search_fields = ['user__email', 'course__name']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
