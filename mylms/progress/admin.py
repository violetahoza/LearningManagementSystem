from django.contrib import admin
from .models import Progress

class ProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'status', 'last_accessed')
    list_filter = ('status', 'lesson__course')
    search_fields = ('user__username', 'lesson__title')
    date_hierarchy = 'last_accessed'
    
admin.site.register(Progress, ProgressAdmin)