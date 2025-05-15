from django.db import models
from django.utils import timezone
from accounts.models import User

class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def get_lessons_count(self):
        return self.lessons.count()
    
    def get_enrollments_count(self):
        return self.enrollments.count()
    
    def is_active(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date