from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from .models import (
    Admin, Instructor, Student, Course, Category, Lesson, Quiz, 
    Enrollment, Notification, LessonCompletion, QuizResult, Internship,
    InternshipMaterial, InternshipQuiz, InternshipProject, InternshipEnrollment
)
from functools import wraps
import os
import json
import uuid
from django.db import IntegrityError


# Helper Decorators
def admin_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('admin_id'):
            messages.error(request, "Please log in as admin.")
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def instructor_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('instructor_id'):
            messages.error(request, "Please log in as an instructor.")
            return redirect('instructor_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def student_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('student_id'):
            messages.error(request, "Please log in as a student.")
            return redirect('student_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def index(request):
    courses = Course.objects.all().order_by('-created_at')[:6] # Simplified pagination for now
    return render(request, 'lms/list.html', {'courses': courses})

def detail(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    is_enrolled = False
    student_id = request.session.get('student_id')
    if student_id:
        if Enrollment.objects.filter(student_id=student_id, course_id=course.id).exists():
            is_enrolled = True
    return render(request, 'lms/detail.html', {'course': course, 'is_enrolled': is_enrolled})

# ===========================
# ADMIN AUTH
# ===========================

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        try:
            admin = Admin.objects.get(username=username)
            if admin.check_password(password):
                request.session.clear()
                request.session['admin_id'] = admin.id
                messages.success(request, "Logged in successfully.")
                return redirect('index')
            else:
                messages.error(request, "Invalid username or password.")
        except Admin.DoesNotExist:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'lms/admin_login.html')

def admin_logout(request):
    request.session.pop('admin_id', None)
    messages.info(request, "Logged out.")
    return redirect('index')

# ===========================
# STUDENT AUTH
# ===========================

def student_register(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        if Student.objects.filter(username=username).exists() or Student.objects.filter(email=email).exists():
            messages.error(request, "Username or email already taken.")
        else:
            try:
                student = Student(username=username, email=email, full_name=full_name)
                student.set_password(password)
                student.save()
                messages.success(request, "Registered successfully. Please login.")
                return redirect('student_login')
            except IntegrityError:
                messages.error(request, "An account with this email or username already exists.")
            
    return render(request, 'lms/student_register.html')

def student_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        try:
            student = Student.objects.get(username=username)
            if student.check_password(password):
                request.session.clear()
                request.session['student_id'] = student.id
                messages.success(request, "Logged in successfully.")
                return redirect('student_dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        except Student.DoesNotExist:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'lms/student_login.html')

def student_logout(request):
    request.session.pop('student_id', None)
    messages.info(request, "Logged out.")
    return redirect('index')

# ===========================
# INSTRUCTOR AUTH
# ===========================

def instructor_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        try:
            instructor = Instructor.objects.get(username=username)
            if instructor.check_password(password):
                request.session.clear()
                request.session['instructor_id'] = instructor.id
                messages.success(request, "Logged in successfully.")
                return redirect('instructor_dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        except Instructor.DoesNotExist:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'lms/instructor_login.html')

def instructor_logout(request):
    request.session.pop('instructor_id', None)
    messages.info(request, "Logged out.")
    return redirect('index')

@instructor_login_required
def instructor_dashboard(request):
    instructor = Instructor.objects.get(id=request.session['instructor_id'])
    courses = instructor.courses.all()
    return render(request, 'lms/instructor_dashboard.html', {'instructor': instructor, 'courses': courses})

# ===========================
# COURSE MGT (Instructor)
# ===========================

@instructor_login_required
def instructor_create_course(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category_id = request.POST.get('category_id')
        description = request.POST.get('description', '').strip()
        
        image_file = 'default.jpg'
        if 'image_file' in request.FILES:
            # Basic file handling - in prod use default_storage or model FileField
            f = request.FILES['image_file']
            filename = f"{uuid.uuid4().hex[:8]}_{f.name}"
            # Need to save to MEDIA_ROOT
            with open(os.path.join(settings.MEDIA_ROOT, filename), 'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)
            image_file = filename

        instructor_id = request.session['instructor_id']
        category = Category.objects.get(id=category_id)
        
        course = Course(
            title=title, 
            category=category, 
            description=description, 
            instructor_id=instructor_id, 
            status='Proposed',
            image_file=image_file
        )
        course.save()
        messages.success(request, "Course created successfully.")
        return redirect('instructor_dashboard')
        
    return render(request, 'lms/create_course_v2.html', {'categories': categories, 'is_instructor': True})

@instructor_login_required
def instructor_manage_lessons(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if course.instructor_id != request.session['instructor_id']:
        messages.error(request, "Unauthorized.")
        return redirect('instructor_dashboard')
        
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        
        video_file = None
        notes_file = None
        
        if 'video_file' in request.FILES:
            f = request.FILES['video_file']
            filename = f"vid_{uuid.uuid4().hex[:8]}_{f.name}"
            with open(os.path.join(settings.MEDIA_ROOT, filename), 'wb+') as dest:
                for chunk in f.chunks():
                    dest.write(chunk)
            video_file = filename
            
        if 'notes_file' in request.FILES:
            f = request.FILES['notes_file']
            filename = f"note_{uuid.uuid4().hex[:8]}_{f.name}"
            with open(os.path.join(settings.MEDIA_ROOT, filename), 'wb+') as dest:
                for chunk in f.chunks():
                    dest.write(chunk)
            notes_file = filename
            
        Lesson.objects.create(
            course=course, title=title, content=content, video_file=video_file, notes_file=notes_file
        )
        messages.success(request, "Lesson added.")
    
    return render(request, 'lms/instructor_lessons.html', {'course': course})

# ===========================
# STUDENT DASHBOARD
# ===========================

@student_login_required
def student_dashboard(request):
    student = Student.objects.get(id=request.session['student_id'])
    enrollments = student.enrollments.all()
    notifications = Notification.objects.filter(student=student, is_read=False)
    return render(request, 'lms/student_dashboard.html', {'student': student, 'enrollments': enrollments, 'notifications': notifications})

@student_login_required
def enroll_course(request, course_id):
    if request.method == 'POST':
        student_id = request.session['student_id']
        course = get_object_or_404(Course, id=course_id)
        
        if not Enrollment.objects.filter(student_id=student_id, course_id=course.id).exists():
            Enrollment.objects.create(student_id=student_id, course_id=course.id)
            messages.success(request, "Enrolled successfully.")
        else:
            messages.info(request, "Already enrolled.")
            
        return redirect('student_dashboard')
    return redirect('index')

@student_login_required
def student_learn(request, course_id):
    student_id = request.session['student_id']
    enrollment = get_object_or_404(Enrollment, student_id=student_id, course_id=course_id)
    return render(request, 'lms/learn.html', {'course': enrollment.course, 'student': enrollment.student})

@student_login_required
def student_notifications(request):
    student_id = request.session['student_id']
    student = Student.objects.get(id=student_id)
    notifications = Notification.objects.filter(student=student).order_by('-created_at')
    
    # Mark all as read when viewed? Or user manually marks? 
    # For now just list them. Often viewing them marks as read.
    # Let's keep it simple as per original flask app if possible, 
    # or just list them. The template splits by new/old or just lists all.
    # The flask template logic was "if notifications".
    
    return render(request, 'lms/student_notifications.html', {'notifications': notifications})


# ===========================
# MISSING VIEWS IMPLEMENTATION
# ===========================

@admin_login_required
def admin_internships(request):
    internships = Internship.objects.all()
    return render(request, 'lms/admin_internships.html', {'internships': internships})

@admin_login_required
def admin_internship_submissions(request):
    submissions = InternshipEnrollment.objects.filter(project_submission__isnull=False).order_by('-completed_at')
    return render(request, 'lms/admin_internship_submissions.html', {'submissions': submissions})

@admin_login_required
def admin_create_internship(request):
    instructors = Instructor.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        duration = request.POST.get('duration', '').strip()
        instructor_id = request.POST.get('instructor_id')
        
        if title:
            Internship.objects.create(
                title=title, description=description, duration=duration, 
                instructor_id=instructor_id if instructor_id else None
            )
            messages.success(request, "Internship created successfully.")
            return redirect('admin_internships')
        else:
            messages.error(request, "Title is required.")
            
    return render(request, 'lms/admin_create_internship.html', {'instructors': instructors})

@admin_login_required
def admin_edit_internship(request, internship_id):
    internship = get_object_or_404(Internship, id=internship_id)
    instructors = Instructor.objects.all()
    
    if request.method == 'POST':
        # Update basics
        if "update_details" in request.POST:
            internship.title = request.POST.get('title', '').strip()
            internship.description = request.POST.get('description', '').strip()
            internship.duration = request.POST.get('duration', '').strip()
            if instructor_id:
                internship.instructor_id = instructor_id
            else:
                internship.instructor_id = None
            internship.save()
            messages.success(request, "Details updated.")
        
        # Add Material
        elif "add_material" in request.POST:
            title = request.POST.get('mat_title', '').strip()
            if 'mat_file' in request.FILES:
                f = request.FILES['mat_file']
                filename = f"int_mat_{uuid.uuid4().hex[:8]}_{f.name}"
                if not os.path.exists(settings.MEDIA_ROOT):
                    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
                with open(os.path.join(settings.MEDIA_ROOT, filename), 'wb+') as dest:
                    for chunk in f.chunks():
                        dest.write(chunk)
                
                InternshipMaterial.objects.create(
                    internship=internship, title=title, file_path=filename
                )
                messages.success(request, "Material added.")
        
        # Create Quiz
        elif "create_quiz" in request.POST:
            title = request.POST.get('quiz_title', '').strip()
            questions = request.POST.get('questions_json')
            if title and questions:
                InternshipQuiz.objects.create(
                    internship=internship, title=title, questions_data=questions
                )
                messages.success(request, "Quiz added.")
            else:
                messages.error(request, "Quiz title and questions required.")

        # Set Project
        elif "set_project" in request.POST:
            title = request.POST.get('proj_title', '').strip()
            desc = request.POST.get('proj_desc', '').strip()
            
            proj, created = InternshipProject.objects.get_or_create(internship=internship)
            proj.title = title
            proj.description = desc
            proj.save()
            messages.success(request, "Project definition updated.")

        return redirect('admin_edit_internship', internship_id=internship.id)

    return render(request, 'lms/admin_edit_internship_v2.html', {'internship': internship, 'instructors': instructors})

@admin_login_required
def admin_review_submission(request, enrollment_id, action):
    enrollment = get_object_or_404(InternshipEnrollment, id=enrollment_id)
    
    if request.method == 'POST':
        if action == "approve":
            enrollment.project_status = "Approved"
            enrollment.status = "Completed"
            enrollment.completed_at = timezone.now()
            enrollment.certificate_id = str(uuid.uuid4()).upper()
            messages.success(request, "Submission approved. Certificate generated.")
        elif action == "reject":
            enrollment.project_status = "Rejected"
            messages.warning(request, "Submission rejected.")
            
        enrollment.save()
            
    return redirect('admin_internship_submissions')

@admin_login_required
def admin_view_enrollments(request):
    enrollments = Enrollment.objects.all().order_by('-created_at')
    return render(request, 'lms/admin_enrollments.html', {'enrollments': enrollments})

@admin_login_required
def admin_instructors(request):
    instructors = Instructor.objects.all()
    return render(request, 'lms/admin_instructors.html', {'instructors': instructors})

@admin_login_required
def admin_students(request):
    students = Student.objects.all()
    return render(request, 'lms/admin_students.html', {'students': students})

@admin_login_required
def admin_reports(request):
    total_students = Student.objects.count()
    total_courses = Course.objects.count()
    total_enrollments = Enrollment.objects.count()
    course_stats = []
    for c in Course.objects.all():
        course_stats.append({
            'title': c.title,
            'created_at': c.created_at,
            'enrollments': c.enrollments.count(),
            'status': c.status
        })
    return render(request, 'lms/admin_reports.html', {
        'total_students': total_students, 
        'total_courses': total_courses, 
        'total_enrollments': total_enrollments, 
        'course_stats': course_stats
    })

@admin_login_required
def admin_create_instructor(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        
        if Instructor.objects.filter(username=username).exists():
             messages.error(request, "Username taken.")
        else:
             instructor = Instructor(
                 username=username, email=email, full_name=full_name
             )
             instructor.set_password(password)
             instructor.save()
             messages.success(request, "Instructor created.")
             return redirect('admin_instructors')
             
    return render(request, 'lms/admin_create_instructor.html')

@admin_login_required
def admin_delete_instructor(request, id):
    instructor = get_object_or_404(Instructor, id=id)
    if request.method == "POST":
        instructor.delete()
        messages.success(request, "Instructor deleted.")
    return redirect('admin_instructors')

@admin_login_required
def admin_delete_student(request, id):
    student = get_object_or_404(Student, id=id)
    if request.method == "POST":
        student.delete()
        messages.success(request, "Student deleted.")
    return redirect('admin_students')


@admin_login_required
def admin_create_course(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category_id = request.POST.get('category_id')
        description = request.POST.get('description', '').strip()
        
        image_file = 'default.jpg'
        if 'image_file' in request.FILES:
            f = request.FILES['image_file']
            filename = f"{uuid.uuid4().hex[:8]}_{f.name}"
            with open(os.path.join(settings.MEDIA_ROOT, filename), 'wb+') as dest:
                for chunk in f.chunks():
                    dest.write(chunk)
            image_file = filename

        category = Category.objects.get(id=category_id)
        Course.objects.create(
            title=title, 
            category=category, 
            description=description, 
            status='Approved', 
            image_file=image_file
        )
        messages.success(request, "Course created (Approved).")
        return redirect('index')
        
    return render(request, 'lms/create_course_v2.html', {'categories': categories})



def student_internship_list(request):
    internships = Internship.objects.all()
    return render(request, 'lms/internship_list.html', {'internships': internships})

@student_login_required
def student_enroll_internship(request, internship_id):
    if request.method == 'POST':
        student_id = request.session['student_id']
        internship = get_object_or_404(Internship, id=internship_id)
        
        if not InternshipEnrollment.objects.filter(student_id=student_id, internship_id=internship.id).exists():
            InternshipEnrollment.objects.create(student_id=student_id, internship_id=internship.id)
            messages.success(request, "Enrolled in internship!")
        else:
            messages.info(request, "Already enrolled.")
            
        return redirect('student_view_internship', internship_id=internship.id)
    return redirect('student_internship_list')

@student_login_required
def student_view_internship(request, internship_id):
    student_id = request.session['student_id']
    enrollment = InternshipEnrollment.objects.filter(student_id=student_id, internship_id=internship_id).first()
    
    if not enrollment:
        messages.warning(request, "Please enroll first.")
        return redirect('student_internship_list')
        
    internship = get_object_or_404(Internship, id=internship_id)
    
    if request.method == 'POST':
        if 'project_file' in request.FILES:
            f = request.FILES['project_file']
            filename = f"proj_sub_{uuid.uuid4().hex[:8]}_{f.name}" 
            # In prod use FileField/Storage
            with open(os.path.join(settings.MEDIA_ROOT, filename), 'wb+') as dest:
                for chunk in f.chunks():
                    dest.write(chunk)
            
            enrollment.project_submission = filename
            enrollment.project_status = "Submitted"
            enrollment.save()
            messages.success(request, "Project submitted for review!")
            return redirect('student_view_internship', internship_id=internship.id)

    return render(request, 'lms/student_internship_view.html', {'internship': internship, 'enrollment': enrollment})

@student_login_required
def student_take_internship_quiz(request, internship_id, quiz_id):
    internship = get_object_or_404(Internship, id=internship_id)
    quiz = get_object_or_404(InternshipQuiz, id=quiz_id)
    student_id = request.session['student_id']
    
    # Verify enrollment
    if not InternshipEnrollment.objects.filter(student_id=student_id, internship_id=internship.id).exists():
         messages.error(request, "Enroll first.")
         return redirect('student_internship_list')

    if request.method == "POST":
        questions = json.loads(quiz.questions_data) if quiz.questions_data else []
        score = 0
        total = len(questions)
        
        for i, q in enumerate(questions):
            ans = request.POST.get(f"q_{i}")
            if ans == q.get('correct'):
               score += 1
        
        percentage = (score / total) * 100 if total > 0 else 0
        messages.info(request, f"Quiz completed. Score: {percentage:.1f}%")
        return redirect('student_view_internship', internship_id=internship.id)

    questions = json.loads(quiz.questions_data) if quiz.questions_data else []
    return render(request, 'lms/take_internship_quiz.html', {'internship': internship, 'quiz': quiz, 'questions': questions})

@student_login_required
def student_internship_certificate(request, internship_id):
    student_id = request.session['student_id']
    enrollment = InternshipEnrollment.objects.filter(student_id=student_id, internship_id=internship_id).first()
    
    if not enrollment or enrollment.project_status != "Approved":
        messages.error(request, "Certificate not available yet.")
        return redirect('student_view_internship', internship_id=internship_id)
        
    return render(request, 'lms/internship_certificate.html', {
        'student': enrollment.student, 
        'internship': enrollment.internship, 
        'date': enrollment.completed_at,
        'cert_id': enrollment.certificate_id
    })

@student_login_required
def student_profile(request):
    student = Student.objects.get(id=request.session['student_id'])
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        if full_name:
            student.full_name = full_name
        
        if email:
            if not Student.objects.filter(email=email).exclude(id=student.id).exists():
                student.email = email
            else:
                messages.error(request, "Email already taken.")
        
        if password:
            student.set_password(password)
            
        student.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('student_profile')
        
    return render(request, 'lms/student_profile.html', {'student': student})
