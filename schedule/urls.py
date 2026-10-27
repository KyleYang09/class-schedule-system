from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('classes/', views.class_timetable, name='class_index'),
    path('classes/<int:pk>/', views.class_timetable, name='class_timetable'),
    path('teachers/', views.teacher_timetable, name='teacher_index'),
    path('teachers/<int:pk>/', views.teacher_timetable, name='teacher_timetable'),
    path('my/', views.my_timetable, name='my_timetable'),
    path("han/", views.py_han, name="py_han"),
]
