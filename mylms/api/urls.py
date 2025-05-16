from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'courses', views.CourseViewSet, basename='api-course')
router.register(r'lessons', views.LessonViewSet, basename='api-lesson')
router.register(r'quizzes', views.QuizViewSet, basename='api-quiz')
router.register(r'questions', views.QuestionViewSet, basename='api-question')
router.register(r'enrollments', views.EnrollmentViewSet, basename='api-enrollment')
router.register(r'progress', views.ProgressViewSet, basename='api-progress')
router.register(r'certificates', views.CertificateViewSet, basename='api-certificate')
router.register(r'notifications', views.NotificationViewSet, basename='api-notification')
router.register(r'users', views.UserViewSet, basename='api-user')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', views.LoginAPIView.as_view(), name='api-login'),
    path('auth/register/', views.RegisterAPIView.as_view(), name='api-register'),
    path('auth/refresh-token/', views.TokenRefreshAPIView.as_view(), name='api-token-refresh'),
    path('documentation/', views.api_documentation, name='api-documentation'),
]