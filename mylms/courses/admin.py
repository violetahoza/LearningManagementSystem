from django.contrib import admin
from .models import Course

class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'start_date', 'end_date', 'is_active', 'get_enrollments_count')
    list_filter = ('instructor', 'start_date', 'end_date')
    search_fields = ('title', 'description', 'instructor__username')
    date_hierarchy = 'created_at'
    
    def get_enrollments_count(self, obj):
        return obj.get_enrollments_count()
    get_enrollments_count.short_description = 'Enrollments'
    
admin.site.register(Course, CourseAdmin)