from django.db import models
from accounts.models import User
from courses.models import Course

class Enrollment(models.Model):
    ENROLLED = 'enrolled'
    COMPLETED = 'completed'
    DROPPED = 'dropped'
    
    STATUS_CHOICES = [
        (ENROLLED, 'Enrolled'),
        (COMPLETED, 'Completed'),
        (DROPPED, 'Dropped'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=ENROLLED)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'course')
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title}"