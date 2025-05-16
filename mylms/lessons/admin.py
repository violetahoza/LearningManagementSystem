from django.contrib import admin
from .models import Lesson

class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'created_at')
    list_filter = ('course',)
    search_fields = ('title', 'content', 'course__title')
    date_hierarchy = 'created_at'
    
admin.site.register(Lesson, LessonAdmin)