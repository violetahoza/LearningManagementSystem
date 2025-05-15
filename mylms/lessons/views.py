from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
import json
from .models import Lesson
from .forms import LessonForm, LessonOrderForm
from courses.models import Course
from enrollments.models import Enrollment
from progress.models import Progress

@login_required
def lesson_detail(request, lesson_id):
    """View a lesson"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    
    # Check if the user is the instructor
    is_instructor = request.user == course.instructor or request.user.is_admin()
    
    # If not instructor, check if the student is enrolled
    is_enrolled = False
    if not is_instructor and request.user.is_student():
        enrollment = Enrollment.objects.filter(
            user=request.user,
            course=course,
            status=Enrollment.ENROLLED
        ).exists()
        
        if not enrollment:
            messages.error(request, "You must be enrolled in this course to view its lessons.")
            return redirect('courses:course_detail', course_id=course.id)
        
        is_enrolled = True
        
        # Update progress status
        progress, created = Progress.objects.get_or_create(
            user=request.user,
            lesson=lesson,
            defaults={'status': Progress.IN_PROGRESS}
        )
        
        if progress.status == Progress.NOT_STARTED:
            progress.status = Progress.IN_PROGRESS
            progress.save()
    
    # Get previous and next lessons for navigation
    lessons = Lesson.objects.filter(course=course).order_by('order')
    
    prev_lesson = None
    next_lesson = None
    
    for i, current_lesson in enumerate(lessons):
        if current_lesson.id == lesson.id:
            if i > 0:
                prev_lesson = lessons[i - 1]
            if i < len(lessons) - 1:
                next_lesson = lessons[i + 1]
    
    # Get progress status for student
    progress_status = None
    if request.user.is_student():
        progress = Progress.objects.filter(
            user=request.user,
            lesson=lesson
        ).first()
        
        if progress:
            progress_status = progress.status
        else:
            progress_status = Progress.NOT_STARTED
    
    context = {
        'lesson': lesson,
        'course': course,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'is_instructor': is_instructor,
        'is_enrolled': is_enrolled,
        'progress_status': progress_status
    }
    return render(request, 'lessons/lesson_detail.html', context)

@login_required
def mark_lesson_complete(request, lesson_id):
    """Mark a lesson as completed"""
    if not request.user.is_student():
        return HttpResponseForbidden("Only students can mark lessons as completed.")
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    
    # Check if enrolled
    enrollment = get_object_or_404(
        Enrollment, 
        user=request.user,
        course=course,
        status=Enrollment.ENROLLED
    )
    
    # Update progress
    progress, created = Progress.objects.get_or_create(
        user=request.user,
        lesson=lesson,
        defaults={'status': Progress.COMPLETED}
    )
    
    if not created:
        progress.status = Progress.COMPLETED
        progress.save()
    
    messages.success(request, f'Lesson "{lesson.title}" marked as completed!')
    
    # Get next lesson for redirect
    next_lesson = Lesson.objects.filter(
        course=course,
        order__gt=lesson.order
    ).order_by('order').first()
    
    if next_lesson:
        return redirect('lessons:lesson_detail', lesson_id=next_lesson.id)
    else:
        # No more lessons, redirect to course page
        return redirect('courses:course_detail', course_id=course.id)

@login_required
def create_lesson(request, course_id):
    """Create a new lesson"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the instructor or admin
    if course.instructor != request.user and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    # Calculate next order value
    next_order = 1
    last_lesson = Lesson.objects.filter(course=course).order_by('-order').first()
    if last_lesson:
        next_order = last_lesson.order + 1
    
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            
            # Create notification for enrolled students
            from notifications.models import Notification
            enrolled_users = User.objects.filter(
                enrollments__course=course,
                enrollments__status=Enrollment.ENROLLED
            )
            
            for user in enrolled_users:
                Notification.objects.create(
                    user=user,
                    title=f"New Lesson: {lesson.title}",
                    message=f"A new lesson has been added to the course {course.title}.",
                    notification_type=Notification.LESSON_ADDED
                )
            
            messages.success(request, f'Lesson "{lesson.title}" has been created.')
            return redirect('courses:course_detail', course_id=course.id)
    else:
        form = LessonForm(initial={'order': next_order})
    
    context = {
        'form': form,
        'course': course,
        'action': 'Create'
    }
    return render(request, 'lessons/lesson_form.html', context)

@login_required
def edit_lesson(request, lesson_id):
    """Edit an existing lesson"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    
    # Check if user is the instructor or admin
    if course.instructor != request.user and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, f'Lesson "{lesson.title}" has been updated.')
            return redirect('courses:course_detail', course_id=course.id)
    else:
        form = LessonForm(instance=lesson)
    
    context = {
        'form': form,
        'lesson': lesson,
        'course': course,
        'action': 'Edit'
    }
    return render(request, 'lessons/lesson_form.html', context)

@login_required
def delete_lesson(request, lesson_id):
    """Delete a lesson"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    
    # Check if user is the instructor or admin
    if course.instructor != request.user and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    if request.method == 'POST':
        lesson_title = lesson.title
        lesson.delete()
        messages.success(request, f'Lesson "{lesson_title}" has been deleted.')
        return redirect('courses:course_detail', course_id=course.id)
    
    context = {
        'lesson': lesson,
        'course': course
    }
    return render(request, 'lessons/lesson_confirm_delete.html', context)

@login_required
def reorder_lessons(request, course_id):
    """Reorder lessons for a course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the instructor or admin
    if course.instructor != request.user and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    lessons = Lesson.objects.filter(course=course).order_by('order')
    
    if request.method == 'POST':
        form = LessonOrderForm(request.POST)
        if form.is_valid():
            order_data = json.loads(form.cleaned_data['lesson_order'])
            
            for lesson_id, new_order in order_data.items():
                lesson = Lesson.objects.get(id=int(lesson_id))
                lesson.order = new_order
                lesson.save()
            
            messages.success(request, 'Lesson order has been updated.')
            return redirect('courses:course_detail', course_id=course.id)
    else:
        form = LessonOrderForm()
    
    context = {
        'form': form,
        'course': course,
        'lessons': lessons
    }
    return render(request, 'lessons/reorder_lessons.html', context)