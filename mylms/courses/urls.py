from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Student views
    path('', views.course_list, name='course_list'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    
    # Teacher views
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('create/', views.create_course, name='create_course'),
    path('<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('<int:course_id>/delete/', views.delete_course, name='delete_course'),
    path('<int:course_id>/students/', views.course_students, name='course_students'),
    path('<int:course_id>/statistics/', views.course_statistics, name='course_statistics'),
]