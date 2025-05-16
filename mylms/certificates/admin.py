from django.contrib import admin
from .models import Certificate

class CertificateAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'certificate_code', 'issue_date')
    list_filter = ('course',)
    search_fields = ('user__username', 'course__title', 'certificate_code')
    date_hierarchy = 'issue_date'
    readonly_fields = ('certificate_code', 'issue_date')
    
admin.site.register(Certificate, CertificateAdmin)