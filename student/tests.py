from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User
from dormitory.models import University, Dormitory, Floor, RoomType, Room
from .models import Student, Application, ApplicationDocument
from datetime import date, timedelta
from django.core.files.uploadedfile import SimpleUploadedFile

class StudentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='studentuser',
            email='student@example.com',
            password='studentpass123',
            role=User.STUDENT,
            first_name='Test',
            last_name='Student'
        )
        self.university = University.objects.create(
            name='Test University',
            address='Test Address',
            description='Test Description',
            contact_info='test@university.com',
            website='https://testuniversity.com'
        )
        self.student = Student.objects.create(
            user=self.user,
            university=self.university,
            student_id='S12345',
            faculty='Engineering',
            course=2,
            emergency_contact='Parent: +998901234567',
            passport_number='AA1234567',
            passport_issue_date=date(2020, 1, 1),
            passport_expiry_date=date(2030, 1, 1)
        )

    def test_student_creation(self):
        self.assertEqual(str(self.student), f"{self.user.get_full_name()} - {self.student.student_id}")
        self.assertEqual(self.student.university, self.university)

class ApplicationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='studentuser',
            email='student@example.com',
            password='studentpass123',
            role=User.STUDENT
        )
        self.university = University.objects.create(
            name='Test University',
            address='Test Address',
            description='Test Description',
            contact_info='test@university.com',
            website='https://testuniversity.com'
        )
        self.dormitory = Dormitory.objects.create(
            name='Test Dormitory',
            address='Test Address',
            university=self.university,
            admin=None,
            floors_number=5,
            rooms_number=50,
            description='Test Description',
            contact_info='test@dormitory.com',
            status='active',
            subscription_end_date=date.today() + timedelta(days=365),
            latitude=41.311081,
            longitude=69.240562
        )
        self.student = Student.objects.create(
            user=self.user,
            university=self.university,
            student_id='S12345',
            faculty='Engineering',
            course=2,
            emergency_contact='Parent: +998901234567',
            passport_number='AA1234567',
            passport_issue_date=date(2020, 1, 1),
            passport_expiry_date=date(2030, 1, 1)
        )
        self.application = Application.objects.create(
            student=self.student,
            dormitory=self.dormitory,
            preferred_room_type='Standard',
            status='pending'
        )

    def test_application_creation(self):
        self.assertEqual(str(self.application), f"Application by {self.student.user.username} for {self.dormitory.name}")
        self.assertEqual(self.application.status, 'pending')

class StudentAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.super_admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role=User.SUPER_ADMIN
        )
        self.student_user = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='studentpass123',
            role=User.STUDENT
        )
        self.university = University.objects.create(
            name='Test University',
            address='Test Address',
            description='Test Description',
            contact_info='test@university.com',
            website='https://testuniversity.com'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            university=self.university,
            student_id='S12345',
            faculty='Engineering',
            course=2,
            emergency_contact='Parent: +998901234567',
            passport_number='AA1234567',
            passport_issue_date=date(2020, 1, 1),
            passport_expiry_date=date(2030, 1, 1)
        )

    def test_student_list(self):
        self.client.force_authenticate(user=self.super_admin)
        url = reverse('student-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated and non-paginated responses
        data = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        self.assertTrue(any(s['student_id'] == 'S12345' for s in data))

    def test_student_detail(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('student-detail', args=[self.student.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['student_id'], 'S12345')

    def test_student_update(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('student-detail', args=[self.student.id])
        data = {'faculty': 'Mathematics'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student.refresh_from_db()
        self.assertEqual(self.student.faculty, 'Mathematics')

class ApplicationAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.super_admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role=User.SUPER_ADMIN
        )
        self.student_user = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='studentpass123',
            role=User.STUDENT
        )
        self.university = University.objects.create(
            name='Test University',
            address='Test Address',
            description='Test Description',
            contact_info='test@university.com',
            website='https://testuniversity.com'
        )
        self.dormitory = Dormitory.objects.create(
            name='Test Dormitory',
            address='Test Address',
            university=self.university,
            admin=None,
            floors_number=5,
            rooms_number=50,
            description='Test Description',
            contact_info='test@dormitory.com',
            status='active',
            subscription_end_date=date.today() + timedelta(days=365),
            latitude=41.311081,
            longitude=69.240562
        )
        self.student = Student.objects.create(
            user=self.student_user,
            university=self.university,
            student_id='S12345',
            faculty='Engineering',
            course=2,
            emergency_contact='Parent: +998901234567',
            passport_number='AA1234567',
            passport_issue_date=date(2020, 1, 1),
            passport_expiry_date=date(2030, 1, 1)
        )
        self.application = Application.objects.create(
            student=self.student,
            dormitory=self.dormitory,
            preferred_room_type='Standard',
            status='pending'
        )

    def test_application_list(self):
        self.client.force_authenticate(user=self.super_admin)
        url = reverse('application-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        self.assertTrue(any(a['preferred_room_type'] == 'Standard' for a in data))

    def test_application_detail(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('application-detail', args=[self.application.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['preferred_room_type'], 'Standard')

    def test_application_update(self):
        self.client.force_authenticate(user=self.super_admin)
        url = reverse('application-detail', args=[self.application.id])
        data = {'status': 'approved'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'approved')

class ApplicationDocumentAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.super_admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role=User.SUPER_ADMIN
        )
        self.student_user = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='studentpass123',
            role=User.STUDENT
        )
        self.university = University.objects.create(
            name='Test University',
            address='Test Address',
            description='Test Description',
            contact_info='test@university.com',
            website='https://testuniversity.com'
        )
        self.dormitory = Dormitory.objects.create(
            name='Test Dormitory',
            address='Test Address',
            university=self.university,
            admin=None,
            floors_number=5,
            rooms_number=50,
            description='Test Description',
            contact_info='test@dormitory.com',
            status='active',
            subscription_end_date=date.today() + timedelta(days=365),
            latitude=41.311081,
            longitude=69.240562
        )
        self.student = Student.objects.create(
            user=self.student_user,
            university=self.university,
            student_id='S12345',
            faculty='Engineering',
            course=2,
            emergency_contact='Parent: +998901234567',
            passport_number='AA1234567',
            passport_issue_date=date(2020, 1, 1),
            passport_expiry_date=date(2030, 1, 1)
        )
        self.application = Application.objects.create(
            student=self.student,
            dormitory=self.dormitory,
            preferred_room_type='Standard',
            status='pending'
        )
        self.document = ApplicationDocument.objects.create(
            application=self.application,
            document_type='passport',
            document=SimpleUploadedFile("test.pdf", b"file_content")
        )

    def test_document_list(self):
        self.client.force_authenticate(user=self.super_admin)
        url = reverse('applicationdocument-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        self.assertTrue(any(d['document_type'] == 'passport' for d in data))

    def test_document_detail(self):
        self.client.force_authenticate(user=self.student_user)
        url = reverse('applicationdocument-detail', args=[self.document.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['document_type'], 'passport')

    def test_document_update(self):
        self.client.force_authenticate(user=self.super_admin)
        url = reverse('applicationdocument-detail', args=[self.document.id])
        data = {'document_type': 'photo'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.document.refresh_from_db()
        self.assertEqual(self.document.document_type, 'photo')