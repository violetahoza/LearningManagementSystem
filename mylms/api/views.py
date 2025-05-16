from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from accounts.models import User
from accounts.serializers import UserSerializer, RegisterSerializer, LoginSerializer
from courses.models import Course
from courses.serializers import CourseSerializer, CourseDetailSerializer
from lessons.models import Lesson
from lessons.serializers import LessonSerializer, LessonDetailSerializer
from quizzes.models import Quiz, Question, Answer
from quizzes.serializers import QuizSerializer, QuizDetailSerializer, QuestionSerializer, AnswerSerializer
from enrollments.models import Enrollment
from enrollments.serializers import EnrollmentSerializer
from progress.models import Progress
from progress.serializers import ProgressSerializer, CourseProgressSerializer
from certificates.models import Certificate
from certificates.serializers import CertificateSerializer
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from courses.permissions import IsInstructorOrReadOnly, IsEnrolledOrInstructor
from enrollments.permissions import IsOwnerOrAdmin

class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'token': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': UserSerializer(user).data
                })
            
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'token': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TokenRefreshAPIView(TokenRefreshView):
    """Refresh authentication token"""
    pass

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing users.
    Only admin users can list all users or create/update/delete users.
    Regular users can only view and update their own profiles.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'create', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return User.objects.all()
        return User.objects.filter(id=user.id)

class CourseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing courses.
    Teachers can create and update their own courses.
    Students can view courses they're enrolled in.
    """
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorOrReadOnly]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return Course.objects.all()
        elif user.is_teacher():
            return Course.objects.filter(instructor=user)
        else:  # Student
            return Course.objects.filter(enrollments__user=user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseSerializer
    
    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_courses(self, request):
        """Get courses created by the current user (for instructors)"""
        if request.user.role == 'teacher':
            courses = Course.objects.filter(instructor=request.user)
            serializer = self.get_serializer(courses, many=True)
            return Response(serializer.data)
        return Response({"detail": "You are not an instructor."}, status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=False, methods=['get'])
    def enrolled(self, request):
        """Get courses where the current user is enrolled (for students)"""
        courses = Course.objects.filter(enrollments__user=request.user, enrollments__status='enrolled')
        serializer = self.get_serializer(courses, many=True)
        return Response(serializer.data)

class LessonViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing lessons.
    Teachers can create and update lessons for their courses.
    Students can view lessons for courses they're enrolled in.
    """
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return Lesson.objects.all()
        elif user.is_teacher():
            return Lesson.objects.filter(course__instructor=user)
        else:  # Student
            return Lesson.objects.filter(course__enrollments__user=user, course__enrollments__status='enrolled')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LessonDetailSerializer
        return LessonSerializer
    
    def perform_create(self, serializer):
        course = serializer.validated_data['course']
        if self.request.user != course.instructor and not self.request.user.is_admin():
            raise permissions.PermissionDenied("You can only create lessons for your own courses.")
        serializer.save()

class QuizViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing quizzes.
    Teachers can create and update quizzes for their courses.
    Students can view quizzes for courses they're enrolled in.
    """
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return Quiz.objects.all()
        elif user.is_teacher():
            return Quiz.objects.filter(course__instructor=user)
        else:  # Student
            return Quiz.objects.filter(course__enrollments__user=user, course__enrollments__status='enrolled')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return QuizDetailSerializer
        return QuizSerializer
    
    def perform_create(self, serializer):
        course = serializer.validated_data['course']
        if self.request.user != course.instructor and not self.request.user.is_admin():
            raise permissions.PermissionDenied("You can only create quizzes for your own courses.")
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def submit_answers(self, request, pk=None):
        """
        Submit answers to a quiz.
        Expected format:
        {
            "answers": [
                {"question": 1, "answer_text": "Answer text"},
                {"question": 2, "answer_text": "True"}
            ]
        }
        """
        quiz = self.get_object()
        
        # Check if user is enrolled in the course
        if not Enrollment.objects.filter(user=request.user, course=quiz.course, status='enrolled').exists():
            return Response({"detail": "You are not enrolled in this course."}, status=status.HTTP_403_FORBIDDEN)
        
        answers_data = request.data.get('answers', [])
        results = []
        
        for answer_data in answers_data:
            try:
                question_id = answer_data.get('question')
                answer_text = answer_data.get('answer_text')
                
                question = Question.objects.get(id=question_id, quiz=quiz)
                
                # Create or update answer
                serializer = AnswerSerializer(data={
                    'question': question.id,
                    'answer_text': answer_text
                }, context={'request': request})
                
                if serializer.is_valid():
                    answer = serializer.save()
                    results.append({
                        'question': question.id,
                        'is_correct': answer.is_correct,
                        'marks_obtained': answer.marks_obtained
                    })
                else:
                    results.append({
                        'question': question.id,
                        'error': serializer.errors
                    })
            except Question.DoesNotExist:
                results.append({
                    'question': answer_data.get('question'),
                    'error': 'Question not found or not part of this quiz'
                })
        
        return Response(results)

class QuestionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing quiz questions.
    Teachers can create and update questions for their quizzes.
    Students can view questions for quizzes in courses they're enrolled in.
    """
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return Question.objects.all()
        elif user.is_teacher():
            return Question.objects.filter(quiz__course__instructor=user)
        else:  # Student
            return Question.objects.filter(
                quiz__course__enrollments__user=user, 
                quiz__course__enrollments__status='enrolled'
            )
    
    def perform_create(self, serializer):
        quiz = serializer.validated_data['quiz']
        if self.request.user != quiz.course.instructor and not self.request.user.is_admin():
            raise permissions.PermissionDenied("You can only create questions for your own quizzes.")
        serializer.save()

class EnrollmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing course enrollments.
    Students can enroll in courses and view their enrollments.
    Teachers can view enrollments for their courses.
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return Enrollment.objects.all()
        elif user.is_teacher():
            return Enrollment.objects.filter(course__instructor=user)
        else:  # Student
            return Enrollment.objects.filter(user=user)
    
    @action(detail=False, methods=['post'])
    def enroll(self, request):
        """Enroll the current user in a course"""
        course_id = request.data.get('course_id')
        if not course_id:
            return Response({"detail": "Course ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if already enrolled
        if Enrollment.objects.filter(user=request.user, course=course).exists():
            return Response({"detail": "You are already enrolled in this course."}, status=status.HTTP_400_BAD_REQUEST)
        
        enrollment = Enrollment.objects.create(
            user=request.user,
            course=course,
            status=Enrollment.ENROLLED
        )
        
        # Create notification
        Notification.objects.create(
            user=request.user,
            title=f"Enrollment Confirmation: {course.title}",
            message=f"You have successfully enrolled in the course: {course.title}",
            notification_type=Notification.ENROLLMENT
        )
        
        return Response(EnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)

class ProgressViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing lesson progress.
    Students can update their progress for lessons.
    Teachers can view progress for students in their courses.
    """
    serializer_class = ProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return Progress.objects.all()
        elif user.is_teacher():
            return Progress.objects.filter(lesson__course__instructor=user)
        else:  # Student
            return Progress.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def course_progress(self, request):
        """Get progress for a specific course"""
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response({"detail": "Course ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = CourseProgressSerializer(
            {'course_id': int(course_id)}, 
            context={'request': request}
        )
        return Response(serializer.data)

class CertificateViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing certificates.
    Students can view their certificates.
    Teachers can issue certificates for students in their courses.
    """
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return Certificate.objects.all()
        elif user.is_teacher():
            return Certificate.objects.filter(course__instructor=user)
        else:  # Student
            return Certificate.objects.filter(user=user)
    
    @action(detail=False, methods=['post'])
    def issue(self, request):
        """Issue a certificate for a student"""
        if not request.user.is_teacher() and not request.user.is_admin():
            return Response({"detail": "Only teachers and administrators can issue certificates."}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        course_id = request.data.get('course_id')
        student_id = request.data.get('student_id')
        
        if not course_id or not student_id:
            return Response({"detail": "Course ID and student ID are required."}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        try:
            course = Course.objects.get(id=course_id)
            student = User.objects.get(id=student_id, role=User.STUDENT)
        except (Course.DoesNotExist, User.DoesNotExist):
            return Response({"detail": "Course or student not found."}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        # Check if the teacher is the course instructor
        if not request.user.is_admin() and course.instructor != request.user:
            return Response({"detail": "You can only issue certificates for your courses."}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        # Check if certificate already exists
        if Certificate.objects.filter(user=student, course=course).exists():
            return Response({"detail": "Certificate already exists for this student in this course."}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Check if student is enrolled and has completed the course
        try:
            enrollment = Enrollment.objects.get(user=student, course=course)
        except Enrollment.DoesNotExist:
            return Response({"detail": "Student is not enrolled in this course."}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Create certificate
        certificate = Certificate.objects.create(
            user=student,
            course=course
        )
        
        # Update enrollment status
        enrollment.status = Enrollment.COMPLETED
        enrollment.save()
        
        # Create notification
        Notification.objects.create(
            user=student,
            title=f"Certificate Issued: {course.title}",
            message=f"Congratulations! You have been issued a certificate for completing {course.title}.",
            notification_type=Notification.CERTIFICATE_ISSUED
        )
        
        return Response(CertificateSerializer(certificate).data, status=status.HTTP_201_CREATED)

class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing notifications.
    Users can view and update their own notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"detail": "Notification marked as read."})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"detail": "All notifications marked as read."})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"count": count})

def api_documentation(request):
    """View for API documentation"""
    return render(request, 'api/documentation.html')