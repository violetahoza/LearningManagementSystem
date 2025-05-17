from django.urls import path, include
from . import views
from . import admin_urls 

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
    # Admin related URLs
    path('admin/', include((admin_urls.urlpatterns, 'core'), namespace='admin')),
]