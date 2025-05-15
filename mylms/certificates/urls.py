from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    # Student views
    path('', views.certificate_list, name='certificate_list'),
    path('<int:certificate_id>/', views.certificate_detail, name='certificate_detail'),
    path('<int:certificate_id>/download/', views.download_certificate, name='download_certificate'),
    
    # Teacher views
    path('generate/<int:course_id>/<int:student_id>/', views.generate_certificate, name='generate_certificate'),
    path('verify/<str:certificate_code>/', views.verify_certificate, name='verify_certificate'),
]