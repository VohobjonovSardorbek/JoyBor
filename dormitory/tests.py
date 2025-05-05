from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import (
    University, Picture, Dormitory, Floor, RoomType,
    RoomFacility, Room, RoomBooking
)
from datetime import date, timedelta

User = get_user_model()


class DormitoryModelTest(TestCase):
    def setUp(self):
        # Create test data
        self.university = University.objects.create(
            name='Test University',
            address='Test Address',
            description='Test Description',
            contact_info='test@university.com',
            website='https://testuniversity.com'
        )

        self.super_admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role=User.SUPER_ADMIN,
            first_name='Admin',
            last_name='User'
        )

        self.dormitory_admin = User.objects.create_user(
            username='dormadmin',
            email='dormadmin@example.com',
            password='dormadminpass123',
            role=User.DORMITORY_ADMIN,
            first_name='Dorm',
            last_name='Admin'
        )

        self.student = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='studentpass123',
            role=User.STUDENT,
            first_name='Test',
            last_name='Student'
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
            subscription_end_date=date.today() + timedelta(days=365),
            latitude=41.311081,
            longitude=69.240562
        )

    def test_university_creation(self):
        """Test university model creation and string representation"""
        self.assertEqual(str(self.university), 'Test University')
        self.assertEqual(self.university.name, 'Test University')
        self.assertEqual(self.university.address, 'Test Address')
        self.assertEqual(self.university.website, 'https://testuniversity.com')

    def test_dormitory_creation(self):
        """Test dormitory model creation and relationships"""
        self.assertEqual(str(self.dormitory), 'Test Dormitory')
        self.assertEqual(self.dormitory.university, self.university)
        self.assertEqual(self.dormitory.admin, self.dormitory_admin)
        self.assertEqual(self.dormitory.status, 'active')
        self.assertEqual(self.dormitory.latitude, 41.311081)
        self.assertEqual(self.dormitory.longitude, 69.240562)

    def test_floor_creation(self):
        """Test floor model creation and validation"""
        floor = Floor.objects.create(
            dormitory=self.dormitory,
            floor_number=1,
            rooms_number=10,
            description='Test Floor',
            gender_type='male'
        )
        self.assertEqual(str(floor), 'Floor 1 - Test Dormitory')
        self.assertEqual(floor.gender_type, 'male')

        # Test unique constraint
        with self.assertRaises(Exception):
            Floor.objects.create(
                dormitory=self.dormitory,
                floor_number=1,
                rooms_number=10
            )

    def test_room_type_creation(self):
        """Test room type model creation and validation"""
        room_type = RoomType.objects.create(
            name='Standard',
            capacity=2,
            price_per_month=1000,
            description='Standard Room',
            is_active=True
        )
        self.assertEqual(str(room_type), 'Standard - 2 person(s)')
        self.assertEqual(room_type.capacity, 2)
        self.assertEqual(room_type.price_per_month, 1000)

    def test_room_facility_creation(self):
        """Test room facility model creation"""
        facility = RoomFacility.objects.create(
            name='WiFi',
            description='High-speed internet',
            icon='wifi'
        )
        self.assertEqual(str(facility), 'WiFi')
        self.assertEqual(facility.icon, 'wifi')

    def test_room_creation(self):
        """Test room model creation and relationships"""
        floor = Floor.objects.create(
            dormitory=self.dormitory,
            floor_number=1,
            rooms_number=10,
            gender_type='male'
        )
        room_type = RoomType.objects.create(
            name='Standard',
            capacity=2,
            price_per_month=1000
        )
        facility = RoomFacility.objects.create(
            name='WiFi',
            description='High-speed internet'
        )

        room = Room.objects.create(
            dormitory=self.dormitory,
            floor=floor,
            room_type=room_type,
            room_number='101',
            status='available',
            monthly_price=1000,
            room_type_category='standard',
            equipment={'bed': 2, 'desk': 2}
        )
        room.facilities.add(facility)

        self.assertEqual(str(room), 'Room 101 - Test Dormitory')
        self.assertEqual(room.status, 'available')
        self.assertEqual(room.current_occupancy, 0)
        self.assertEqual(room.monthly_price, 1000)
        self.assertEqual(room.room_type_category, 'standard')
        self.assertEqual(room.equipment, {'bed': 2, 'desk': 2})
        self.assertEqual(room.facilities.count(), 1)

    def test_room_booking_creation(self):
        """Test room booking model creation and status changes"""
        floor = Floor.objects.create(
            dormitory=self.dormitory,
            floor_number=1,
            rooms_number=10,
            gender_type='male'
        )
        room_type = RoomType.objects.create(
            name='Standard',
            capacity=2,
            price_per_month=1000
        )
        room = Room.objects.create(
            dormitory=self.dormitory,
            floor=floor,
            room_type=room_type,
            room_number='101',
            status='available',
            monthly_price=1000
        )

        booking = RoomBooking.objects.create(
            room=room,
            student=self.student,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status='Pending'
        )

        self.assertEqual(str(booking), f'Booking for 101 by student')
        self.assertEqual(booking.status, 'Pending')

        # Test status change
        booking.status = 'Approved'
        booking.save()
        self.assertEqual(booking.status, 'Approved')


class DormitoryAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # Create test users
        self.super_admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role=User.SUPER_ADMIN,
            first_name='Admin',
            last_name='User'
        )

        self.dormitory_admin = User.objects.create_user(
            username='dormadmin',
            email='dormadmin@example.com',
            password='dormadminpass123',
            role=User.DORMITORY_ADMIN,
            first_name='Dorm',
            last_name='Admin'
        )

        self.student = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='studentpass123',
            role=User.STUDENT,
            first_name='Test',
            last_name='Student'
        )

        # Create test university
        self.university = University.objects.create(
            name='Test University',
            address='Test Address',
            description='Test Description',
            contact_info='test@university.com',
            website='https://testuniversity.com'
        )

        # Create test dormitory
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
            subscription_end_date=date.today() + timedelta(days=365),
            latitude=41.311081,
            longitude=69.240562
        )

    def test_university_list(self):
        """Test university list API endpoint"""
        self.client.force_authenticate(user=self.super_admin)
        url = reverse('university-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        # Handle paginated and non-paginated responses
        if isinstance(data, dict) and 'results' in data:
            universities = [u for u in data['results'] if u['name'] == self.university.name]
        else:
            universities = [u for u in data if u['name'] == self.university.name]
        self.assertEqual(len(universities), 1)

    def test_dormitory_creation(self):
        """Test dormitory creation API endpoint"""
        self.client.force_authenticate(user=self.super_admin)
        url = reverse('dormitory-list')
        data = {
            'name': 'New Dormitory',
            'address': 'New Address',
            'university': self.university.id,
            'admin': self.dormitory_admin.id,
            'floors_number': 3,
            'rooms_number': 30,
            'status': 'active',
            'description': 'New Description',
            'contact_info': 'new@dormitory.com',
            'subscription_end_date': (date.today() + timedelta(days=365)).isoformat(),
            'latitude': 41.311081,
            'longitude': 69.240562
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Dormitory.objects.count(), 2)
        new_dormitory = Dormitory.objects.get(name='New Dormitory')
        self.assertEqual(new_dormitory.name, 'New Dormitory')
        self.assertEqual(new_dormitory.latitude, 41.311081)

    def test_room_booking(self):
        """Test room booking API endpoint"""
        self.client.force_authenticate(user=self.student)

        # Create floor
        floor = Floor.objects.create(
            dormitory=self.dormitory,
            floor_number=1,
            rooms_number=10,
            description='Test Floor',
            gender_type='male'
        )

        # Create room type
        room_type = RoomType.objects.create(
            name='Standard',
            capacity=2,
            price_per_month=1000,
            description='Standard Room',
            is_active=True
        )

        # Create room
        room = Room.objects.create(
            dormitory=self.dormitory,
            floor=floor,
            room_type=room_type,
            room_number='101',
            status='available',
            monthly_price=1000,
            room_type_category='standard',
            equipment={'bed': 2, 'desk': 2}
        )

        # Test booking
        url = reverse('room-book', args=[room.id])
        data = {
            'start_date': date.today().isoformat(),
            'end_date': (date.today() + timedelta(days=30)).isoformat()
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RoomBooking.objects.count(), 1)
        booking = RoomBooking.objects.first()
        self.assertEqual(booking.student, self.student)
        self.assertEqual(booking.status, 'Pending')

    def test_room_booking_approval(self):
        """Test room booking approval API endpoint"""
        self.client.force_authenticate(user=self.dormitory_admin)

        # Create floor
        floor = Floor.objects.create(
            dormitory=self.dormitory,
            floor_number=1,
            rooms_number=10,
            description='Test Floor',
            gender_type='male'
        )

        # Create room type
        room_type = RoomType.objects.create(
            name='Standard',
            capacity=2,
            price_per_month=1000,
            description='Standard Room',
            is_active=True
        )

        # Create room
        room = Room.objects.create(
            dormitory=self.dormitory,
            floor=floor,
            room_type=room_type,
            room_number='101',
            status='available',
            monthly_price=1000,
            room_type_category='standard',
            current_occupancy=0
        )

        # Create booking
        booking = RoomBooking.objects.create(
            room=room,
            student=self.student,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status='Pending'
        )

        # Test approval
        url = reverse('roombooking-detail', args=[booking.id])
        data = {
            'status': 'Approved',
            'room_status': 'partially_filled'  # Add room status update
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh objects from database
        booking.refresh_from_db()
        room.refresh_from_db()

        self.assertEqual(booking.status, 'Approved')
        self.assertEqual(room.status, 'partially_filled')
        self.assertEqual(room.current_occupancy, 1)

    def test_room_facility_creation(self):
        """Test room facility creation API endpoint"""
        self.client.force_authenticate(user=self.super_admin)
        url = reverse('roomfacility-list')
        data = {
            'name': 'WiFi',
            'description': 'High-speed internet',
            'icon': 'wifi'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RoomFacility.objects.count(), 1)
        self.assertEqual(RoomFacility.objects.first().name, 'WiFi')

    def test_room_type_creation(self):
        """Test room type creation API endpoint"""
        self.client.force_authenticate(user=self.super_admin)
        url = reverse('roomtype-list')
        data = {
            'name': 'VIP',
            'description': 'VIP Room',
            'capacity': 2,
            'price_per_month': 2000,
            'is_active': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RoomType.objects.count(), 1)
        self.assertEqual(RoomType.objects.first().name, 'VIP')
        self.assertEqual(RoomType.objects.first().price_per_month, 2000)
