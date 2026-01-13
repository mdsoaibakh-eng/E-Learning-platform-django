from django.test import TestCase, Client
from django.urls import reverse
from .models import (
    Student, Notification, Instructor, Admin, Internship, 
    InternshipQuiz, InternshipEnrollment
)

class StudentNotificationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = Student.objects.create(
            username='teststudent',
            email='test@example.com',
            full_name='Test Student'
        )
        self.student.set_password('password')
        self.student.save()
        
        self.notification = Notification.objects.create(
            student=self.student,
            message='Test Notification'
        )

    def test_student_notifications_view(self):
        # Login
        session = self.client.session
        session['student_id'] = self.student.id
        session.save()
        
        response = self.client.get(reverse('student_notifications'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Notification')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Notification')
        self.assertContains(response, 'My Notifications')

class InternshipTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = Student.objects.create(username='student', email='s@test.com', full_name='Student')
        self.student.set_password('pass')
        self.student.save()
        
        self.instructor = Instructor.objects.create(username='instructor', email='i@test.com')
        self.instructor.set_password('pass')
        self.instructor.save()
        
        self.admin = Admin.objects.create(username='admin')
        self.admin.set_password('pass')
        self.admin.save()
        
        self.internship = Internship.objects.create(
            title='Test Internship',
            description='Desc',
            duration='1 Month',
            instructor=self.instructor
        )
        
        self.quiz = InternshipQuiz.objects.create(
            internship=self.internship,
            title='Test Quiz',
            questions_data='[{"text": "Q1", "options": ["A", "B"], "correct": "A"}]'
        )

    def test_internship_flow(self):
        # 1. Student Enroll
        session = self.client.session
        session['student_id'] = self.student.id
        session.save()
        
        resp = self.client.post(reverse('student_enroll_internship', args=[self.internship.id]))
        self.assertEqual(resp.status_code, 302) # Redirects to view
        self.assertTrue(InternshipEnrollment.objects.filter(student=self.student, internship=self.internship).exists())
        
        # 2. Student Take Quiz
        resp = self.client.post(reverse('student_take_internship_quiz', args=[self.internship.id, self.quiz.id]), {
            'q_0': 'A'
        })
        self.assertEqual(resp.status_code, 302)
        
        # 3. Student Submit Project (Mock file)
        from django.core.files.uploadedfile import SimpleUploadedFile
        f = SimpleUploadedFile("proj.pdf", b"content", content_type="application/pdf")
        resp = self.client.post(reverse('student_view_internship', args=[self.internship.id]), {
            'project_file': f
        })
        self.assertEqual(resp.status_code, 302)
        enrollment = InternshipEnrollment.objects.get(student=self.student, internship=self.internship)
        self.assertEqual(enrollment.project_status, 'Submitted')
        
        # 4. Admin Approve
        session = self.client.session
        session['admin_id'] = self.admin.id
        session.save()
        
        resp = self.client.post(reverse('admin_review_submission', args=[enrollment.id, 'approve']))
        self.assertEqual(resp.status_code, 302)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.project_status, 'Approved')
        self.assertIsNotNone(enrollment.certificate_id)
        
        # 5. Student View Certificate
        session = self.client.session
        session['student_id'] = self.student.id
        session.save()
        
        resp = self.client.get(reverse('student_internship_certificate', args=[self.internship.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Certificate of Completion')
