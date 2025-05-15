import json
from rest_framework import serializers
from .models import Quiz, Question, Answer
from courses.models import Course
from accounts.models import User

class QuestionSerializer(serializers.ModelSerializer):
    options_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = ['id', 'quiz', 'question_text', 'question_type', 
                  'options', 'options_list']
        read_only_fields = ['options_list']
        extra_kwargs = {
            'correct_answer': {'write_only': True}  # Hide correct answer from students
        }
    
    def get_options_list(self, obj):
        if obj.options and obj.question_type == Question.MULTIPLE_CHOICE:
            try:
                return json.loads(obj.options)
            except:
                return []
        return []
    
    def validate(self, attrs):
        # Validate that multiple choice questions have options
        if attrs.get('question_type') == Question.MULTIPLE_CHOICE and not attrs.get('options'):
            raise serializers.ValidationError(
                {"options": "Multiple choice questions must have options."}
            )
        return attrs

class QuizSerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = ['id', 'course', 'title', 'total_marks', 
                  'questions_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_questions_count(self, obj):
        return obj.questions.count()
    
    def validate_course(self, value):
        user = self.context['request'].user
        # Only instructors who own the course can create/update quizzes
        if user.is_teacher() and value.instructor != user:
            raise serializers.ValidationError("You can only create quizzes for courses you instruct.")
        return value

class QuizDetailSerializer(QuizSerializer):
    questions = QuestionSerializer(many=True, read_only=True, source='questions.all')
    
    class Meta(QuizSerializer.Meta):
        fields = QuizSerializer.Meta.fields + ['questions']

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'question', 'user', 'answer_text', 
                  'is_correct', 'marks_obtained', 'submitted_at']
        read_only_fields = ['user', 'is_correct', 'marks_obtained', 'submitted_at']
    
    def create(self, validated_data):
        # Set the user to the current request user
        validated_data['user'] = self.context['request'].user
        
        # Check if answer already exists for this user and question
        question = validated_data.get('question')
        user = validated_data.get('user')
        
        existing_answer = Answer.objects.filter(question=question, user=user).first()
        if existing_answer:
            # Update existing answer instead of creating a new one
            existing_answer.answer_text = validated_data.get('answer_text')
            existing_answer.save()
            self.grade_answer(existing_answer)
            return existing_answer
        
        # Create a new answer and grade it
        answer = Answer.objects.create(**validated_data)
        self.grade_answer(answer)
        return answer
    
    def grade_answer(self, answer):
        question = answer.question
        
        # Auto-grading logic
        if question.question_type == Question.TRUE_FALSE or question.question_type == Question.MULTIPLE_CHOICE:
            # For T/F and multiple choice, exact match required
            is_correct = answer.answer_text.lower().strip() == question.correct_answer.lower().strip()
            answer.is_correct = is_correct
            answer.marks_obtained = question.quiz.total_marks / question.quiz.questions.count() if is_correct else 0
        
        elif question.question_type == Question.SHORT_ANSWER:
            # For short answer, we could implement more sophisticated grading
            # Here we're using a simple contains check
            student_answer = answer.answer_text.lower().strip()
            correct_answer = question.correct_answer.lower().strip()
            
            if student_answer == correct_answer:
                # Exact match
                answer.is_correct = True
                answer.marks_obtained = question.quiz.total_marks / question.quiz.questions.count()
            elif correct_answer in student_answer or student_answer in correct_answer:
                # Partial match
                answer.is_correct = False  # Not fully correct
                answer.marks_obtained = (question.quiz.total_marks / question.quiz.questions.count()) * 0.5  # 50% credit
            else:
                # No match
                answer.is_correct = False
                answer.marks_obtained = 0
        
        answer.save()
        
        # Create notification for graded quiz
        try:
            from notifications.models import Notification
            
            # Check if we've graded all questions in the quiz
            quiz = question.quiz
            user = answer.user
            
            questions_count = quiz.questions.count()
            answered_questions = Answer.objects.filter(
                question__quiz=quiz,
                user=user
            ).count()
            
            if answered_questions == questions_count:
                # All questions answered, create a notification
                total_score = Answer.objects.filter(
                    question__quiz=quiz,
                    user=user
                ).aggregate(models.Sum('marks_obtained'))['marks_obtained__sum']
                
                message = f"You scored {total_score} out of {quiz.total_marks} on {quiz.title}."
                Notification.objects.create(
                    user=user,
                    title=f"Quiz Graded: {quiz.title}",
                    message=message,
                    notification_type=Notification.QUIZ_GRADED
                )
        except:
            # Fail silently if notification creation fails
            pass