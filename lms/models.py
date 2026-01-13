from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
import uuid

class Admin(models.Model):
    username = models.CharField(max_length=120, unique=True)
    password_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    def set_password(self, password):
        self.password_hash = make_password(password)

    def check_password(self, password):
        return check_password(password, self.password_hash)

    def __str__(self):
        return f"Admin {self.username}"

class Instructor(models.Model):
    username = models.CharField(max_length=120, unique=True)
    full_name = models.CharField(max_length=150, null=True, blank=True)
    email = models.CharField(max_length=120, unique=True, null=True, blank=True)
    password_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    def set_password(self, password):
        self.password_hash = make_password(password)

    def check_password(self, password):
        return check_password(password, self.password_hash)

    def __str__(self):
        return f"Instructor {self.username}"

class Student(models.Model):
    username = models.CharField(max_length=120, unique=True)
    full_name = models.CharField(max_length=150, null=True, blank=True)
    email = models.CharField(max_length=120, unique=True)
    password_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    def set_password(self, password):
        self.password_hash = make_password(password)

    def check_password(self, password):
        return check_password(password, self.password_hash)
    
    def __str__(self):
        return f"Student {self.username}"

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.name

class Course(models.Model):
    title = models.CharField(max_length=120)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='courses')
    description = models.TextField(null=True, blank=True)
    image_file = models.CharField(max_length=120, null=True, blank=True, default='default.jpg')
    
    instructor = models.ForeignKey(Instructor, on_delete=models.SET_NULL, null=True, related_name='courses')
    status = models.CharField(max_length=50, default='Proposed') # Proposed, Approved, Rejected
    
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Course {self.title}"

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=150)
    content = models.TextField(null=True, blank=True) # Could be video URL or text
    video_file = models.CharField(max_length=100, null=True, blank=True) # MP4 filename
    notes_file = models.CharField(max_length=100, null=True, blank=True) # PDF filename
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=150)
    questions_data = models.TextField(null=True, blank=True) # JSON or Text
    created_at = models.DateTimeField(default=timezone.now)

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=50, default='Active') # Active, Completed
    progress = models.FloatField(default=0.0)
    certificate_id = models.CharField(max_length=50, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

class Notification(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

class LessonCompletion(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(default=timezone.now)

class QuizResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.FloatField()
    passed = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(default=timezone.now)

# ===========================
# INTERNSHIP MODELS
# ===========================

class Internship(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    duration = models.CharField(max_length=50, null=True, blank=True) # e.g. "3 Months"
    instructor = models.ForeignKey(Instructor, on_delete=models.SET_NULL, null=True, related_name='internships')
    created_at = models.DateTimeField(default=timezone.now)

class InternshipMaterial(models.Model):
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=150)
    resource_type = models.CharField(max_length=50, default='pdf') # pdf, video
    file_path = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

class InternshipQuiz(models.Model):
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=150)
    questions_data = models.TextField(null=True, blank=True) # JSON
    created_at = models.DateTimeField(default=timezone.now)

class InternshipProject(models.Model):
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=150)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

class InternshipEnrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='internship_enrollments')
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=50, default='Active') # Active, Completed
    
    project_submission = models.CharField(max_length=255, null=True, blank=True) # File path
    project_status = models.CharField(max_length=50, default='Pending') # Pending, Submitted, Approved, Rejected
    
    certificate_id = models.CharField(max_length=50, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
