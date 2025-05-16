from django.contrib import admin
from .models import Enrollment

class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'status', 'enrolled_at', 'updated_at')
    list_filter = ('status', 'course')
    search_fields = ('user__username', 'course__title')
    date_hierarchy = 'enrolled_at'
    
admin.site.register(Enrollment, EnrollmentAdmin)