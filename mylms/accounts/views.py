from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, RegisterForm, ProfileForm, CustomPasswordChangeForm
import logging

# Get logger
logger = logging.getLogger('user_activity')

def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            
            if user:
                login(request, user)
                logger.info(f"User {username} logged in successfully")
                next_url = request.GET.get('next', 'core:dashboard')
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect(next_url)
            else:
                logger.warning(f"Failed login attempt for username {username}")
                messages.error(request, 'Invalid username or password')
    else:
        form = LoginForm()
    
    context = {'form': form}
    return render(request, 'accounts/login.html', context)

def user_logout(request):
    """User logout view"""
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        logger.info(f"User {username} logged out successfully")
        messages.success(request, 'You have been successfully logged out.')
    return redirect('core:home')

def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            logger.info(f"New user registered: {user.username}")
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to our learning platform.')
            return redirect('core:dashboard')
    else:
        form = RegisterForm()
    
    context = {'form': form}
    return render(request, 'accounts/register.html', context)

@login_required
def profile(request):
    """User profile view"""
    user = request.user
    
    # Get user statistics based on role
    if user.is_student():
        enrolled_courses_count = user.enrollments.count()
        completed_courses_count = user.enrollments.filter(status='completed').count()
        certificates_count = user.certificates.count()
        
        context = {
            'user': user,
            'enrolled_courses_count': enrolled_courses_count,
            'completed_courses_count': completed_courses_count,
            'certificates_count': certificates_count
        }
    elif user.is_teacher():
        courses_count = user.courses.count()
        students_count = user.courses.annotate(students=models.Count('enrollments')).aggregate(total=models.Sum('students'))['total'] or 0
        active_courses_count = user.courses.filter(
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date()
        ).count()
        
        context = {
            'user': user,
            'courses_count': courses_count,
            'students_count': students_count,
            'active_courses_count': active_courses_count
        }
    else:  # Admin
        context = {'user': user}
    
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    """Edit user profile view"""
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            logger.info(f"User {request.user.username} updated their profile")
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)
    
    context = {'form': form}
    return render(request, 'accounts/edit_profile.html', context)

@login_required
def change_password(request):
    """Change password view"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Important: update the session to prevent logging out
            update_session_auth_hash(request, user)
            logger.info(f"User {request.user.username} changed their password")
            messages.success(request, 'Your password has been updated.')
            return redirect('accounts:profile')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    context = {'form': form}
    return render(request, 'accounts/change_password.html', context)