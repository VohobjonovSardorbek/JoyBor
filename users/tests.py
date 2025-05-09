from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role=User.STUDENT,
            first_name='Test',
            last_name='User'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            phone_number='+1234567890'
        )

    def test_user_creation(self):
        self.assertEqual(str(self.user), 'testuser - Student')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertEqual(self.user.role, User.STUDENT)

    def test_user_profile_creation(self):
        self.assertEqual(str(self.profile), 'Profile of testuser')
        self.assertEqual(self.profile.phone_number, '+1234567890')
        self.assertEqual(self.profile.status, 'active')

class UserAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.super_admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role=User.SUPER_ADMIN,
            first_name='Admin',
            last_name='User'
        )
        self.student = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='studentpass123',
            role=User.STUDENT,
            first_name='Test',
            last_name='Student'
        )

    def test_user_registration(self):
        url = reverse('user-register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'confirm_password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'phone_number': '+1234567890',
            'role': User.STUDENT
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('access' in response.data)
        self.assertTrue('refresh' in response.data)

    def test_user_login(self):
        url = reverse('user-login')
        data = {
            'username': 'student',
            'password': 'studentpass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access' in response.data)
        self.assertTrue('refresh' in response.data)

    def test_user_list(self):
        self.client.force_authenticate(user=self.super_admin)
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        active_users = User.objects.filter(is_active=True).count()
        data = response.data
        if isinstance(data, dict) and 'results' in data:
            users = data['results']
        else:
            users = data
    self.assertEqual(len(users), active_users)

    def test_user_detail(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('user-detail', args=[self.student.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'student')

    def test_password_change(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('user-change-password')
        data = {
            'old_password': 'studentpass123',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.student.check_password('newpass123'))

    def test_password_reset_request(self):
        url = reverse('user-reset-password-request')
        data = {'email': 'student@example.com'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class UserProfileAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.super_admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role=User.SUPER_ADMIN,
            first_name='Admin',
            last_name='User'
        )
        self.student = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='studentpass123',
            role=User.STUDENT,
            first_name='Test',
            last_name='Student'
        )
        self.profile = UserProfile.objects.create(
            user=self.student,
            phone_number='+1234567890'
        )

    def test_profile_list(self):
        self.client.force_authenticate(user=self.super_admin)
        url = reverse('userprofile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        active_profiles = UserProfile.objects.filter(user__is_active=True).count()
        data = response.data
        if isinstance(data, dict) and 'results' in data:
            profiles = data['results']
        else:
            profiles = data
        self.assertEqual(len(profiles), active_profiles)

    def test_profile_detail(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('userprofile-detail', args=[self.profile.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], '+1234567890')

    def test_profile_update(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('userprofile-detail', args=[self.profile.id])
        data = {'phone_number': '+9876543210'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone_number, '+9876543210')
