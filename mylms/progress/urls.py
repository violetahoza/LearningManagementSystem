from django.urls import path
from . import views

app_name = 'progress'

urlpatterns = [
    # Student views
    path('course/<int:course_id>/', views.course_progress, name='course_progress'),
    path('<int:progress_id>/update/', views.update_progress, name='update_progress'),
    
    # Teacher views
    path('student/<int:student_id>/course/<int:course_id>/', views.student_progress, name='student_progress'),
]