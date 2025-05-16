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

@login_required
def quiz_detail(request, quiz_id):
    """View quiz details"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    course = quiz.course
    
    # Check if user is the instructor
    is_instructor = request.user == course.instructor or request.user.is_admin()
    
    # Check if student is enrolled
    is_enrolled = False
    user_status = None
    
    if request.user.is_student():
        enrollment = Enrollment.objects.filter(
            user=request.user,
            course=course,
            status=Enrollment.ENROLLED
        ).exists()
        
        is_enrolled = enrollment
        
        if is_enrolled:
            # Get user's quiz status
            questions = Question.objects.filter(quiz=quiz)
            answers = Answer.objects.filter(
                question__in=questions,
                user=request.user
            )
            
            total_questions = questions.count()
            answered_questions = answers.values('question').distinct().count()
            
            if answered_questions == 0:
                user_status = 'not_started'
            elif answered_questions < total_questions:
                user_status = 'in_progress'
            else:
                user_status = 'completed'
    
    # Get questions
    questions = Question.objects.filter(quiz=quiz).order_by('id')
    
    # Add options list for multiple choice questions
    for question in questions:
        if question.question_type == Question.MULTIPLE_CHOICE and question.options:
            try:
                question.options_list = json.loads(question.options)
            except:
                question.options_list = []
    
    context = {
        'quiz': quiz,
        'course': course,
        'is_instructor': is_instructor,
        'is_enrolled': is_enrolled,
        'user_status': user_status,
        'questions': questions
    }
    return render(request, 'quizzes/quiz_detail.html', context)

@login_required
def quiz_attempt(request, quiz_id):
    """Attempt a quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    course = quiz.course
    
    # Check if student is enrolled
    if request.user.is_student():
        enrollment = get_object_or_404(
            Enrollment, 
            user=request.user,
            course=course,
            status=Enrollment.ENROLLED
        )
    else:
        return HttpResponseForbidden("Only enrolled students can attempt quizzes.")
    
    # Get questions
    questions = Question.objects.filter(quiz=quiz).order_by('id')
    
    # Check if user has already completed the quiz
    answers = Answer.objects.filter(
        question__in=questions,
        user=request.user
    )
    
    if answers.count() == questions.count():
        messages.info(request, "You have already completed this quiz. Here are your results.")
        return redirect('quizzes:quiz_results', quiz_id=quiz.id)
    
    # Create dynamic form for quiz questions
    form = QuizAttemptForm(questions=questions)
    
    # Pre-fill with any existing answers
    if answers.exists():
        for answer in answers:
            field_name = f'question_{answer.question.id}'
            if field_name in form.fields:
                form.fields[field_name].initial = answer.answer_text
    
    context = {
        'quiz': quiz,
        'form': form,
        'questions': questions
    }
    return render(request, 'quizzes/quiz_attempt.html', context)

@login_required
def quiz_submit(request, quiz_id):
    """Submit quiz answers"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    course = quiz.course
    
    # Check if student is enrolled
    if request.user.is_student():
        enrollment = get_object_or_404(
            Enrollment, 
            user=request.user,
            course=course,
            status=Enrollment.ENROLLED
        )
    else:
        return HttpResponseForbidden("Only enrolled students can submit quizzes.")
    
    # Get questions
    questions = Question.objects.filter(quiz=quiz).order_by('id')
    
    if request.method == 'POST':
        form = QuizAttemptForm(request.POST, questions=questions)
        
        if form.is_valid():
            # Process each answer
            for question in questions:
                field_name = f'question_{question.id}'
                answer_text = form.cleaned_data.get(field_name)
                
                # Determine if answer is correct
                is_correct = False
                marks_obtained = 0
                
                if question.question_type == Question.MULTIPLE_CHOICE or question.question_type == Question.TRUE_FALSE:
                    # For MCQ and T/F, exact match required
                    is_correct = answer_text.lower().strip() == question.correct_answer.lower().strip()
                    marks_obtained = (quiz.total_marks / questions.count()) if is_correct else 0
                elif question.question_type == Question.SHORT_ANSWER:
                    # For short answer, more flexible matching
                    student_answer = answer_text.lower().strip()
                    correct_answer = question.correct_answer.lower().strip()
                    
                    if student_answer == correct_answer:
                        # Exact match
                        is_correct = True
                        marks_obtained = quiz.total_marks / questions.count()
                    elif correct_answer in student_answer or student_answer in correct_answer:
                        # Partial match
                        is_correct = False
                        marks_obtained = (quiz.total_marks / questions.count()) * 0.5
                    else:
                        # No match
                        is_correct = False
                        marks_obtained = 0
                
                # Create or update answer
                answer, created = Answer.objects.update_or_create(
                    question=question,
                    user=request.user,
                    defaults={
                        'answer_text': answer_text,
                        'is_correct': is_correct,
                        'marks_obtained': marks_obtained
                    }
                )
            
            # Create notification for quiz completion
            total_score = Answer.objects.filter(
                question__quiz=quiz,
                user=request.user
            ).aggregate(Sum('marks_obtained'))['marks_obtained__sum'] or 0
            
            notification_message = f"You scored {total_score:.2f} out of {quiz.total_marks} on {quiz.title}."
            
            Notification.objects.create(
                user=request.user,
                title=f"Quiz Completed: {quiz.title}",
                message=notification_message,
                notification_type=Notification.QUIZ_GRADED
            )
            
            messages.success(request, "Quiz submitted successfully!")
            return redirect('quizzes:quiz_results', quiz_id=quiz.id)
    
    # If form invalid or GET request, redirect back to quiz attempt
    return redirect('quizzes:quiz_attempt', quiz_id=quiz.id)

@login_required
def quiz_results(request, quiz_id):
    """View quiz results"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    course = quiz.course
    
    # Check if student is enrolled
    if request.user.is_student():
        enrollment = get_object_or_404(
            Enrollment, 
            user=request.user,
            course=course
        )
    elif not request.user.is_teacher() and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    # Get questions and answers
    questions = Question.objects.filter(quiz=quiz)
    answers = Answer.objects.filter(
        question__in=questions,
        user=request.user
    ).select_related('question').order_by('question__id')
    
    # Check if user has attempted the quiz
    if not answers.exists():
        messages.warning(request, "You haven't attempted this quiz yet.")
        return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
    
    # Calculate total score and percentage
    total_score = answers.aggregate(Sum('marks_obtained'))['marks_obtained__sum'] or 0
    percentage = (total_score / quiz.total_marks * 100) if quiz.total_marks > 0 else 0
    
    # Count correct answers
    correct_count = answers.filter(is_correct=True).count()
    
    context = {
        'quiz': quiz,
        'answers': answers,
        'total_score': total_score,
        'percentage': round(percentage, 2),
        'correct_count': correct_count
    }
    return render(request, 'quizzes/quiz_results.html', context)

@login_required
def create_quiz(request, course_id):
    """Create a new quiz"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the instructor or admin
    if course.instructor != request.user and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.course = course
            quiz.save()
            messages.success(request, f'Quiz "{quiz.title}" has been created.')
            return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
    else:
        form = QuizForm()
    
    context = {
        'form': form,
        'course': course,
        'action': 'Create'
    }
    return render(request, 'quizzes/quiz_form.html', context)

@login_required
def edit_quiz(request, quiz_id):
    """Edit an existing quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    course = quiz.course
    
    # Check if user is the instructor or admin
    if course.instructor != request.user and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, f'Quiz "{quiz.title}" has been updated.')
            return redirect('quizzes:quiz_detail', quiz_id=quiz.id)
    else:
        form = QuizForm(instance=quiz)
    
    context = {
        'form': form,
        'quiz': quiz,
        'course': course,
        'action': 'Edit'
    }
    return render(request, 'quizzes/quiz_form.html', context)