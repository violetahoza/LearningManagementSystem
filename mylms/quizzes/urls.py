from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    # Student views
    path('<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('<int:quiz_id>/attempt/', views.quiz_attempt, name='quiz_attempt'),
    path('<int:quiz_id>/submit/', views.quiz_submit, name='quiz_submit'),
    path('<int:quiz_id>/results/', views.quiz_results, name='quiz_results'),
    
    # Teacher views
    path('course/<int:course_id>/create/', views.create_quiz, name='create_quiz'),
    path('<int:quiz_id>/edit/', views.edit_quiz, name='edit_quiz'),
    path('<int:quiz_id>/delete/', views.delete_quiz, name='delete_quiz'),
    path('<int:quiz_id>/questions/create/', views.create_question, name='create_question'),
    path('questions/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('questions/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('<int:quiz_id>/statistics/', views.quiz_statistics, name='quiz_statistics'),
]