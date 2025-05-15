from django.urls import path
from . import views

app_name = 'lessons'

urlpatterns = [
    # Student views
    path('<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('<int:lesson_id>/mark-complete/', views.mark_lesson_complete, name='mark_complete'),
    
    # Teacher views
    path('course/<int:course_id>/create/', views.create_lesson, name='create_lesson'),
    path('<int:lesson_id>/edit/', views.edit_lesson, name='edit_lesson'),
    path('<int:lesson_id>/delete/', views.delete_lesson, name='delete_lesson'),
    path('course/<int:course_id>/reorder/', views.reorder_lessons, name='reorder_lessons'),
]