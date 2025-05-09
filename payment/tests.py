from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from users.models import User
from dormitory.models import Dormitory, Room
from .models import PaymentType, PaymentStatus, PaymentTransaction, Subscription
from .permissions import IsSuperAdmin, IsDormitoryAdmin, IsStudent, IsPaymentOwner, IsSubscriptionOwner

# ... existing imports ...
from dormitory.models import University, Floor, RoomType

class PaymentModelsTest(TestCase):
    def setUp(self):
        self.super_admin = User.objects.create_user(
            username='superadmin',
            password='testpass123',
            role=User.SUPER_ADMIN
        )
        self.dormitory_admin = User.objects.create_user(
            username='dormadmin',
            password='testpass123',
            role=User.DORMITORY_ADMIN
        )
        self.student = User.objects.create_user(
            username='student',
            password='testpass123',
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
            admin=self.dormitory_admin,
            floors_number=5,
            rooms_number=50,
            description='Test Description',
            contact_info='test@dormitory.com',
            status='active',
            subscription_end_date=timezone.now().date() + timedelta(days=365),
            latitude=41.311081,
            longitude=69.240562
        )
        self.floor = Floor.objects.create(
            dormitory=self.dormitory,
            floor_number=1,
            rooms_number=10,
            description='Test Floor',
            gender_type='male'
        )
        self.room_type = RoomType.objects.create(
            name='Standard',
            capacity=2,
            price_per_month=1000,
            description='Standard Room',
            is_active=True
        )
        self.room = Room.objects.create(
            dormitory=self.dormitory,
            floor=self.floor,
            room_type=self.room_type,
            room_number='101',
            status='available',
            monthly_price=1000,
            room_type_category='standard',
            equipment={'bed': 2, 'desk': 2}
        )
        self.payment_type = PaymentType.objects.create(
            name='Monthly Rent',
            description='Monthly room rent payment',
            amount=1000
        )
        self.payment_status = PaymentStatus.objects.create(
            name='pending',
            description='Payment is pending'
        )
    # ... rest of your tests ...
class PaymentPermissionsTest(TestCase):
    def setUp(self):
        self.super_admin = User.objects.create_user(
            username='superadmin',
            password='testpass123',
            role=User.SUPER_ADMIN
        )
        self.dormitory_admin = User.objects.create_user(
            username='dormadmin',
            password='testpass123',
            role=User.DORMITORY_ADMIN
        )
        self.student = User.objects.create_user(
            username='student',
            password='testpass123',
            role=User.STUDENT
        )
        
        self.dormitory = Dormitory.objects.create(
            name='Test Dormitory',
            admin=self.dormitory_admin
        )
        
        self.room = Room.objects.create(
            dormitory=self.dormitory,
            room_number='101',
            capacity=2,
            monthly_price=1000
        )
        
        self.payment_type = PaymentType.objects.create(
            name='Monthly Rent',
            description='Monthly room rent payment',
            amount=1000
        )
        
        self.payment_status = PaymentStatus.objects.create(
            name='pending',
            description='Payment is pending'
        )
        
        self.transaction = PaymentTransaction.objects.create(
            student=self.student,
            dormitory=self.dormitory,
            room=self.room,
            payment_type=self.payment_type,
            amount=1000,
            payment_method='bank_transfer',
            status=self.payment_status,
            due_date=timezone.now() + timedelta(days=30)
        )
        
        self.subscription = Subscription.objects.create(
            dormitory=self.dormitory,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=365),
            amount=12000,
            payment_method='bank_transfer',
            payment_status='paid'
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

class PaymentViewsTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.super_admin = User.objects.create_user(
            username='superadmin',
            password='testpass123',
            role=User.SUPER_ADMIN
        )
        self.dormitory_admin = User.objects.create_user(
            username='dormadmin',
            password='testpass123',
            role=User.DORMITORY_ADMIN
        )
        self.student = User.objects.create_user(
            username='student',
            password='testpass123',
            role=User.STUDENT
        )
        
        self.dormitory = Dormitory.objects.create(
            name='Test Dormitory',
            admin=self.dormitory_admin
        )
        
        self.room = Room.objects.create(
            dormitory=self.dormitory,
            room_number='101',
            capacity=2,
            monthly_price=1000
        )
        
        self.payment_type = PaymentType.objects.create(
            name='Monthly Rent',
            description='Monthly room rent payment',
            amount=1000
        )
        
        self.payment_status = PaymentStatus.objects.create(
            name='pending',
            description='Payment is pending'
        )
        
        self.transaction = PaymentTransaction.objects.create(
            student=self.student,
            dormitory=self.dormitory,
            room=self.room,
            payment_type=self.payment_type,
            amount=1000,
            payment_method='bank_transfer',
            status=self.payment_status,
            due_date=timezone.now() + timedelta(days=30)
        )
        
        self.subscription = Subscription.objects.create(
            dormitory=self.dormitory,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=365),
            amount=12000,
            payment_method='bank_transfer',
            payment_status='paid'
        )

    def test_payment_type_list(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(reverse('paymenttype-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_payment_transaction_create(self):
        self.client.force_authenticate(user=self.student)
        data = {
            'dormitory': self.dormitory.id,
            'room': self.room.id,
            'payment_type': self.payment_type.id,
            'amount': 1000,
            'payment_method': 'bank_transfer',
            'status': self.payment_status.id,
            'due_date': (timezone.now() + timedelta(days=30)).isoformat()
        }
        response = self.client.post(reverse('paymenttransaction-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_payment_transaction_statistics(self):
        self.client.force_authenticate(user=self.dormitory_admin)
        response = self.client.get(reverse('paymenttransaction-statistics'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_amount', response.data)
        self.assertIn('total_transactions', response.data)

    def test_subscription_create(self):
        self.client.force_authenticate(user=self.dormitory_admin)
        data = {
            'dormitory': self.dormitory.id,
            'start_date': timezone.now().isoformat(),
            'end_date': (timezone.now() + timedelta(days=365)).isoformat(),
            'amount': 12000,
            'payment_method': 'bank_transfer'
        }
        response = self.client.post(reverse('subscription-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_subscription_statistics(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(reverse('subscription-statistics'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_amount', response.data)
        self.assertIn('total_subscriptions', response.data)
