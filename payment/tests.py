from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User
from dormitory.models import University, Dormitory, Floor, RoomType, Room
from .models import PaymentType, PaymentStatus, PaymentTransaction, Subscription
from datetime import date, timedelta
from django.utils import timezone

# --- Model Tests ---

class PaymentModelsTest(TestCase):
    def setUp(self):
        self.super_admin = User.objects.create_user(
            username='superadmin', password='testpass123', role=User.SUPER_ADMIN
        )
        self.dormitory_admin = User.objects.create_user(
            username='dormadmin', password='testpass123', role=User.DORMITORY_ADMIN
        )
        self.student = User.objects.create_user(
            username='student', password='testpass123', role=User.STUDENT
        )
        self.university = University.objects.create(
            name='Test University', address='Test Address', description='Test Description',
            contact_info='test@university.com', website='https://testuniversity.com'
        )
        self.dormitory = Dormitory.objects.create(
            name='Test Dormitory', address='Test Address', university=self.university,
            admin=self.dormitory_admin, floors_number=5, rooms_number=50,
            description='Test Description', contact_info='test@dormitory.com',
            status='active', subscription_end_date=date.today() + timedelta(days=365),
            latitude=41.311081, longitude=69.240562
        )
        self.floor = Floor.objects.create(
            dormitory=self.dormitory, floor_number=1, rooms_number=10,
            description='Test Floor', gender_type='male'
        )
        self.room_type = RoomType.objects.create(
            name='Standard', capacity=2, price_per_month=1000,
            description='Standard Room', is_active=True
        )
        self.room = Room.objects.create(
            dormitory=self.dormitory, floor=self.floor, room_type=self.room_type,
            room_number='101', status='available', monthly_price=1000,
            room_type_category='standard', equipment={'bed': 2, 'desk': 2}
        )
        self.payment_type = PaymentType.objects.create(
            name='Monthly Rent', description='Monthly room rent payment', amount=1000
        )
        self.payment_status = PaymentStatus.objects.create(
            name='pending', description='Payment is pending'
        )

    def test_payment_type_creation(self):
        self.assertEqual(str(self.payment_type), f"{self.payment_type.name} - {self.payment_type.amount}")
        self.assertTrue(self.payment_type.is_active)

    def test_payment_status_creation(self):
        self.assertEqual(str(self.payment_status), 'pending')

    def test_payment_transaction_creation(self):
        transaction = PaymentTransaction.objects.create(
            student=self.student, dormitory=self.dormitory, room=self.room,
            payment_type=self.payment_type, amount=1000, payment_method='bank_transfer',
            status=self.payment_status, due_date=timezone.now() + timedelta(days=30)
        )
        self.assertIn('Payment', str(transaction))

    def test_subscription_creation(self):
        subscription = Subscription.objects.create(
            dormitory=self.dormitory, start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=365), amount=12000,
            payment_method='bank_transfer', payment_status='paid'
        )
        self.assertIn('Subscription', str(subscription))

# --- Permission Tests ---

from .permissions import IsSuperAdmin, IsDormitoryAdmin, IsStudent, IsPaymentOwner, IsSubscriptionOwner

class PaymentPermissionsTest(TestCase):
    def setUp(self):
        self.super_admin = User.objects.create_user(
            username='superadmin', password='testpass123', role=User.SUPER_ADMIN
        )
        self.dormitory_admin = User.objects.create_user(
            username='dormadmin', password='testpass123', role=User.DORMITORY_ADMIN
        )
        self.student = User.objects.create_user(
            username='student', password='testpass123', role=User.STUDENT
        )
        self.university = University.objects.create(
            name='Test University', address='Test Address', description='Test Description',
            contact_info='test@university.com', website='https://testuniversity.com'
        )
        self.dormitory = Dormitory.objects.create(
            name='Test Dormitory', address='Test Address', university=self.university,
            admin=self.dormitory_admin, floors_number=5, rooms_number=50,
            description='Test Description', contact_info='test@dormitory.com',
            status='active', subscription_end_date=date.today() + timedelta(days=365),
            latitude=41.311081, longitude=69.240562
        )
        self.floor = Floor.objects.create(
            dormitory=self.dormitory, floor_number=1, rooms_number=10,
            description='Test Floor', gender_type='male'
        )
        self.room_type = RoomType.objects.create(
            name='Standard', capacity=2, price_per_month=1000,
            description='Standard Room', is_active=True
        )
        self.room = Room.objects.create(
            dormitory=self.dormitory, floor=self.floor, room_type=self.room_type,
            room_number='101', status='available', monthly_price=1000,
            room_type_category='standard', equipment={'bed': 2, 'desk': 2}
        )
        self.payment_type = PaymentType.objects.create(
            name='Monthly Rent', description='Monthly room rent payment', amount=1000
        )
        self.payment_status = PaymentStatus.objects.create(
            name='pending', description='Payment is pending'
        )
        self.transaction = PaymentTransaction.objects.create(
            student=self.student, dormitory=self.dormitory, room=self.room,
            payment_type=self.payment_type, amount=1000, payment_method='bank_transfer',
            status=self.payment_status, due_date=timezone.now() + timedelta(days=30)
        )
        self.subscription = Subscription.objects.create(
            dormitory=self.dormitory, start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=365), amount=12000,
            payment_method='bank_transfer', payment_status='paid'
        )

    def test_is_super_admin_permission(self):
        permission = IsSuperAdmin()
        request = type('Request', (), {'user': self.super_admin})
        self.assertTrue(permission.has_permission(request, None))
        request = type('Request', (), {'user': self.dormitory_admin})
        self.assertFalse(permission.has_permission(request, None))

    def test_is_dormitory_admin_permission(self):
        permission = IsDormitoryAdmin()
        request = type('Request', (), {'user': self.dormitory_admin})
        self.assertTrue(permission.has_permission(request, None))
        request = type('Request', (), {'user': self.student})
        self.assertFalse(permission.has_permission(request, None))

    def test_is_student_permission(self):
        permission = IsStudent()
        request = type('Request', (), {'user': self.student})
        self.assertTrue(permission.has_permission(request, None))
        request = type('Request', (), {'user': self.dormitory_admin})
        self.assertFalse(permission.has_permission(request, None))

    def test_is_payment_owner_permission(self):
        permission = IsPaymentOwner()
        request = type('Request', (), {'user': self.student})
        self.assertTrue(permission.has_object_permission(request, None, self.transaction))
        request = type('Request', (), {'user': self.dormitory_admin})
        self.assertTrue(permission.has_object_permission(request, None, self.transaction))
        request = type('Request', (), {'user': self.super_admin})
        self.assertTrue(permission.has_object_permission(request, None, self.transaction))

    def test_is_subscription_owner_permission(self):
        permission = IsSubscriptionOwner()
        request = type('Request', (), {'user': self.dormitory_admin})
        self.assertTrue(permission.has_object_permission(request, None, self.subscription))
        request = type('Request', (), {'user': self.super_admin})
        self.assertTrue(permission.has_object_permission(request, None, self.subscription))
        request = type('Request', (), {'user': self.student})
        self.assertFalse(permission.has_object_permission(request, None, self.subscription))

# --- API Tests ---

class PaymentViewsTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.super_admin = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='adminpass123', role=User.SUPER_ADMIN
        )
        self.dormitory_admin = User.objects.create_user(
            username='dormadmin', password='testpass123', role=User.DORMITORY_ADMIN
        )
        self.student = User.objects.create_user(
            username='student', password='testpass123', role=User.STUDENT
        )
        self.university = University.objects.create(
            name='Test University', address='Test Address', description='Test Description',
            contact_info='test@university.com', website='https://testuniversity.com'
        )
        self.dormitory = Dormitory.objects.create(
            name='Test Dormitory', address='Test Address', university=self.university,
            admin=self.dormitory_admin, floors_number=5, rooms_number=50,
            description='Test Description', contact_info='test@dormitory.com',
            status='active', subscription_end_date=date.today() + timedelta(days=365),
            latitude=41.311081, longitude=69.240562
        )
        self.floor = Floor.objects.create(
            dormitory=self.dormitory, floor_number=1, rooms_number=10,
            description='Test Floor', gender_type='male'
        )
        self.room_type = RoomType.objects.create(
            name='Standard', capacity=2, price_per_month=1000,
            description='Standard Room', is_active=True
        )
        self.room = Room.objects.create(
            dormitory=self.dormitory, floor=self.floor, room_type=self.room_type,
            room_number='101', status='available', monthly_price=1000,
            room_type_category='standard', equipment={'bed': 2, 'desk': 2}
        )
        self.payment_type = PaymentType.objects.create(
            name='Monthly Rent', description='Monthly room rent payment', amount=1000
        )
        self.payment_status = PaymentStatus.objects.create(
            name='pending', description='Payment is pending'
        )
        self.transaction = PaymentTransaction.objects.create(
            student=self.student, dormitory=self.dormitory, room=self.room,
            payment_type=self.payment_type, amount=1000, payment_method='bank_transfer',
            status=self.payment_status, due_date=timezone.now() + timedelta(days=30)
        )
        self.subscription = Subscription.objects.create(
            dormitory=self.dormitory, start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=365), amount=12000,
            payment_method='bank_transfer', payment_status='paid'
        )

    def test_payment_type_list(self):
        self.client.force_authenticate(user=self.super_admin)
        url = reverse('paymenttype-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        self.assertTrue(any(pt['name'] == 'Monthly Rent' for pt in data))

    def test_payment_transaction_create(self):
        self.client.force_authenticate(user=self.super_admin)
        url = reverse('paymenttransaction-list')
        data = {
            'student': self.student.id,
            'dormitory': self.dormitory.id,
            'room': self.room.id,
            'payment_type': self.payment_type.id,
            'amount': 1000,
            'payment_method': 'bank_transfer',
            'status': self.payment_status.id,
            'due_date': (timezone.now() + timedelta(days=30)).date()
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_payment_transaction_statistics(self):
        self.client.force_authenticate(user=self.super_admin)
        url = reverse('paymenttransaction-statistics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_amount', response.data)

    def test_subscription_create(self):
        self.client.force_authenticate(user=self.super_admin)
        url = reverse('subscription-list')
        data = {
            'dormitory': self.dormitory.id,
            'start_date': timezone.now().date(),
            'end_date': (timezone.now() + timedelta(days=365)).date(),
            'amount': 12000,
            'payment_method': 'bank_transfer'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_subscription_statistics(self):
        self.client.force_authenticate(user=self.super_admin)
        url = reverse('subscription-statistics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_amount', response.data)