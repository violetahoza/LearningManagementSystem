from django.contrib import admin
from .models import Quiz, Question, Answer

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'total_marks', 'created_at')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')
    date_hierarchy = 'created_at'
    inlines = [QuestionInline]

class AnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'is_correct', 'marks_obtained', 'submitted_at')
    list_filter = ('is_correct', 'question__quiz')
    search_fields = ('user__username', 'question__question_text')
    date_hierarchy = 'submitted_at'
    
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question)
admin.site.register(Answer, AnswerAdmin)