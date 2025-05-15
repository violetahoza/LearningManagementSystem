from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Count, Avg, Sum
import json
from .models import Quiz, Question, Answer
from .forms import QuizForm, QuestionForm, QuizAttemptForm
from courses.models import Course
from enrollments.models import Enrollment
from accounts.models import User

# Previous functions (quiz_detail, quiz_attempt, quiz_submit, quiz_results, create_quiz, edit_quiz) are already implemented

@login_required
def delete_quiz(request, quiz_id):
    """Delete a quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    course = quiz.course
    
    # Check if user is the instructor or admin
    if course.instructor != request.user and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    if request.method == 'POST':
        quiz_title = quiz.title
        quiz.delete()
        messages.success(request, f'Quiz "{quiz_title}" has been deleted.')
        return redirect('courses:course_detail', course_id=course.id)
    
    context = {
        'quiz': quiz,
        'course': course
    }
    return render(request, 'quizzes/quiz_confirm_delete.html', context)

@login_required
def create_question(request, quiz_id):
    """Create a new question for a quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    course = quiz.course
    
    # Check if user is the instructor or admin
    if course.instructor != request.user and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            
            messages.success(request, 'Question has been added to the quiz.')
            
            # Redirect based on the button clicked
            if 'save_and_add' in request.POST:
                return redirect('quizzes:create_question', quiz_id=quiz.id)
            else:
                return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
    else:
        form = QuestionForm()
    
    context = {
        'form': form,
        'quiz': quiz,
        'course': course,
        'action': 'Create',
        'questions_count': Question.objects.filter(quiz=quiz).count()
    }
    return render(request, 'quizzes/question_form.html', context)

@login_required
def edit_question(request, question_id):
    """Edit an existing question"""
    question = get_object_or_404(Question, id=question_id)
    quiz = question.quiz
    course = quiz.course
    
    # Check if user is the instructor or admin
    if course.instructor != request.user and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question has been updated.')
            return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
    else:
        # For multiple choice, convert JSON to newline separated
        if question.question_type == Question.MULTIPLE_CHOICE and question.options:
            options_list = json.loads(question.options)
            question.options = '\n'.join(options_list)
        
        form = QuestionForm(instance=question)
    
    context = {
        'form': form,
        'question': question,
        'quiz': quiz,
        'course': course,
        'action': 'Edit'
    }
    return render(request, 'quizzes/question_form.html', context)

@login_required
def delete_question(request, question_id):
    """Delete a question"""
    question = get_object_or_404(Question, id=question_id)
    quiz = question.quiz
    course = quiz.course
    
    # Check if user is the instructor or admin
    if course.instructor != request.user and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question has been deleted.')
        return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
    
    context = {
        'question': question,
        'quiz': quiz,
        'course': course
    }
    return render(request, 'quizzes/question_confirm_delete.html', context)

@login_required
def quiz_statistics(request, quiz_id):
    """View detailed statistics for a quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    course = quiz.course
    
    # Check if user is the instructor or admin
    if course.instructor != request.user and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    questions = Question.objects.filter(quiz=quiz)
    
    # Overall statistics
    total_attempts = Answer.objects.filter(question__in=questions).values('user').distinct().count()
    
    # Average score
    student_scores = []
    
    if total_attempts > 0:
        students = User.objects.filter(
            answers__question__in=questions
        ).distinct()
        
        for student in students:
            answers = Answer.objects.filter(
                question__in=questions,
                user=student
            )
            
            score = answers.aggregate(Sum('marks_obtained'))['marks_obtained__sum'] or 0
            student_scores.append({
                'student': student,
                'score': score,
                'percentage': (score / quiz.total_marks * 100) if quiz.total_marks > 0 else 0
            })
    
    # Calculate average
    avg_score = 0
    if student_scores:
        avg_score = sum(s['score'] for s in student_scores) / len(student_scores)
    
    # Question statistics
    question_stats = []
    
    for question in questions:
        answers = Answer.objects.filter(question=question)
        correct_answers = answers.filter(is_correct=True).count()
        
        # For multiple choice, get distribution of answers
        answer_distribution = {}
        
        if question.question_type == Question.MULTIPLE_CHOICE:
            options = json.loads(question.options)
            
            # Initialize all options with 0
            for option in options:
                answer_distribution[option] = 0
            
            # Count actual answers
            for answer in answers:
                option = answer.answer_text
                if option in answer_distribution:
                    answer_distribution[option] += 1
        
        question_stats.append({
            'question': question,
            'total_answers': answers.count(),
            'correct_answers': correct_answers,
            'success_rate': (correct_answers / answers.count() * 100) if answers.count() > 0 else 0,
            'answer_distribution': answer_distribution if question.question_type == Question.MULTIPLE_CHOICE else None
        })
    
    context = {
        'quiz': quiz,
        'course': course,
        'total_attempts': total_attempts,
        'avg_score': avg_score,
        'avg_percentage': (avg_score / quiz.total_marks * 100) if quiz.total_marks > 0 else 0,
        'question_stats': question_stats,
        'student_scores': student_scores
    }
    return render(request, 'quizzes/quiz_statistics.html', context)