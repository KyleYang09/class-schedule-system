from django import forms
from django.db import transaction

from .models import ClassGroup, Profile, Teacher

NONE = 'none'
NEW = 'new'


class OnboardingForm(forms.Form):
    role = forms.ChoiceField(
        label='身分',
        choices=Profile.Role.choices,
        widget=forms.RadioSelect,
        error_messages={'required': '請選擇你的身分'},
    )
    class_choice = forms.ChoiceField(label='班級', required=False)
    teacher_choice = forms.ChoiceField(label='教師', required=False)
    new_teacher_name = forms.CharField(label='你的姓名', max_length=50, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['class_choice'].choices = [
            ('', '請選擇班級'),
            *[(str(group.pk), group.name) for group in ClassGroup.objects.all()],
            (NONE, '我不在列表中'),
        ]
        self.fields['teacher_choice'].choices = [
            ('', '請選擇你的姓名'),
            *[(str(teacher.pk), teacher.name) for teacher in Teacher.objects.filter(is_approved=True)],
            (NEW, '找不到我，我要新增'),
        ]

    def clean(self):
        data = super().clean()
        role = data.get('role')
        if role == Profile.Role.STUDENT:
            if not data.get('class_choice'):
                self.add_error('class_choice', '請選擇班級，不在列表中請選「我不在列表中」')
        elif role == Profile.Role.TEACHER:
            choice = data.get('teacher_choice')
            if not choice:
                self.add_error('teacher_choice', '請選擇你的姓名，找不到請選「找不到我，我要新增」')
            elif choice == NEW:
                name = (data.get('new_teacher_name') or '').strip()
                if not name:
                    self.add_error('new_teacher_name', '請輸入你的姓名')
                elif Teacher.objects.filter(name__iexact=name).exists():
                    self.add_error(
                        'new_teacher_name',
                        '已有同名的教師，請從清單選擇；若是同名不同人，請在姓名後加註，例如「王小明（資工）」',
                    )
                else:
                    data['new_teacher_name'] = name
        return data

    def save(self, user):
        role = self.cleaned_data['role']
        with transaction.atomic():
            if role == Profile.Role.STUDENT:
                choice = self.cleaned_data['class_choice']
                return Profile.objects.create(
                    user=user,
                    role=role,
                    class_group=None if choice == NONE else ClassGroup.objects.get(pk=choice),
                )
            choice = self.cleaned_data['teacher_choice']
            if choice == NEW:
                teacher = Teacher.objects.create(
                    name=self.cleaned_data['new_teacher_name'], is_approved=False, created_by=user
                )
            else:
                teacher = Teacher.objects.get(pk=choice)
            return Profile.objects.create(user=user, role=role, teacher=teacher)
