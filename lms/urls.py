from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('course/<int:course_id>/', views.detail, name='detail'),
    
    # Admin
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    # Add other admin paths as implemented in views
    
    # Instructor
    path('instructor/login/', views.instructor_login, name='instructor_login'),
    path('instructor/logout/', views.instructor_logout, name='instructor_logout'),
    path('instructor/dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('instructor/create_course/', views.instructor_create_course, name='instructor_create_course'),
    path('instructor/course/<int:course_id>/lessons/', views.instructor_manage_lessons, name='instructor_manage_lessons'),

    # Student
    path('student/register/', views.student_register, name='student_register'),
    path('student/login/', views.student_login, name='student_login'),
    path('student/logout/', views.student_logout, name='student_logout'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),
    path('student/course/<int:course_id>/learn/', views.student_learn, name='student_learn'),
    path('student/internships/', views.student_internship_list, name='student_internship_list'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/notifications/', views.student_notifications, name='student_notifications'),
    
    path('student/enroll_internship/<int:internship_id>/', views.student_enroll_internship, name='student_enroll_internship'),
    path('student/my_internship/<int:internship_id>/', views.student_view_internship, name='student_view_internship'),
    path('student/internship/<int:internship_id>/quiz/<int:quiz_id>/', views.student_take_internship_quiz, name='student_take_internship_quiz'),
    path('student/internship_certificate/<int:internship_id>/', views.student_internship_certificate, name='student_internship_certificate'),
    
    # Admin (More)
    path('admin/internships/', views.admin_internships, name='admin_internships'),
    path('admin/create_internship/', views.admin_create_internship, name='admin_create_internship'),
    path('admin/edit_internship/<int:internship_id>/', views.admin_edit_internship, name='admin_edit_internship'),
    path('admin/submission/<int:enrollment_id>/<str:action>/', views.admin_review_submission, name='admin_review_submission'),
    path('admin/submissions/', views.admin_internship_submissions, name='admin_internship_submissions'),
    path('admin/enrollments/', views.admin_view_enrollments, name='admin_view_enrollments'),
    path('admin/instructors/', views.admin_instructors, name='admin_instructors'),
    path('admin/students/', views.admin_students, name='admin_students'),
    path('admin/reports/', views.admin_reports, name='admin_reports'),
    path('admin/create_course/', views.admin_create_course, name='admin_create_course'),
    path('admin/create_instructor/', views.admin_create_instructor, name='admin_create_instructor'),
    path('admin/delete_instructor/<int:id>/', views.admin_delete_instructor, name='admin_delete_instructor'),
    path('admin/delete_student/<int:id>/', views.admin_delete_student, name='admin_delete_student'),
    
    path('admin/register/', views.admin_login, name='admin_register'), # Deprecated but keep for link safety if any

]
