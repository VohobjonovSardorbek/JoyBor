from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import (
    University, Picture, Dormitory, Floor, RoomType,
    RoomFacility, Room, RoomBooking
)
from .serializers import (
    UniversitySerializer, PictureSerializer, DormitorySerializer,
    DormitoryCreateSerializer, FloorSerializer, FloorCreateSerializer,
    RoomTypeSerializer, RoomFacilitySerializer, RoomSerializer,
    RoomCreateSerializer, RoomBookingSerializer, RoomBookingCreateSerializer,
    RoomBookingUpdateSerializer
)
from users.permissions import IsSuperAdmin, IsDormitoryAdmin, IsStudent
from django.contrib.auth import get_user_model

User = get_user_model()

# Common swagger parameters
pagination_params = [
    openapi.Parameter(
        'page',
        openapi.IN_QUERY,
        description="Page number",
        type=openapi.TYPE_INTEGER,
        default=1
    ),
    openapi.Parameter(
        'page_size',
        openapi.IN_QUERY,
        description="Number of results per page",
        type=openapi.TYPE_INTEGER,
        default=10
    )
]

ordering_params = [
    openapi.Parameter(
        'ordering',
        openapi.IN_QUERY,
        description="Order by field (prefix with '-' for descending order)",
        type=openapi.TYPE_STRING,
        required=False
    )
]

search_params = [
    openapi.Parameter(
        'search',
        openapi.IN_QUERY,
        description="Search term",
        type=openapi.TYPE_STRING,
        required=False
    )
]

@swagger_auto_schema(
    tags=["Universities"],
    manual_parameters=pagination_params + ordering_params + search_params
)
class UniversityViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing universities.
    """
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['name', 'address']
    search_fields = ['name', 'address', 'description']
    ordering_fields = ['name', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return University.objects.none()
        
        user = self.request.user
        if not user.is_authenticated:
            return University.objects.none()
            
        if user.is_super_admin:
            return University.objects.all()
        elif user.is_dormitory_admin:
            return University.objects.filter(dormitories__admin=user)
        return University.objects.none()

@swagger_auto_schema(
    tags=["Dormitories"],
    manual_parameters=pagination_params + ordering_params + search_params
)
class DormitoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing dormitories.
    """
    queryset = Dormitory.objects.all()
    serializer_class = DormitorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['name', 'university', 'status']
    search_fields = ['name', 'address', 'description']
    ordering_fields = ['name', 'created_at', 'status']

    def get_serializer_class(self):
        if self.action == 'create':
            return DormitoryCreateSerializer
        return DormitorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Dormitory.objects.none()
            
        user = self.request.user
        if not user.is_authenticated:
            return Dormitory.objects.filter(status='active')
            
        if user.is_super_admin:
            return Dormitory.objects.all()
        elif user.is_dormitory_admin:
            return Dormitory.objects.filter(admin=user)
        return Dormitory.objects.filter(status='active')

@swagger_auto_schema(tags=["Dormitories"])
class PictureViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing dormitory pictures.
    """
    queryset = Picture.objects.all()
    serializer_class = PictureSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

    def get_queryset(self):
        dormitory_id = self.request.query_params.get('dormitory_id')
        if dormitory_id:
            return Picture.objects.filter(dormitory_id=dormitory_id)
        return Picture.objects.all()

@swagger_auto_schema(tags=["Dormitories"])
class FloorViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing dormitory floors.
    """
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['dormitory', 'floor_number', 'gender_type']

    def get_serializer_class(self):
        if self.action == 'create':
            return FloorCreateSerializer
        return FloorSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Floor.objects.none()
        user = self.request.user
        if user.is_super_admin:
            return Floor.objects.all()
        elif user.is_dormitory_admin:
            return Floor.objects.filter(dormitory__admin=user)
        return Floor.objects.filter(dormitory__status='active')

@swagger_auto_schema(tags=["Rooms"])
class RoomTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing room types.
    """
    queryset = RoomType.objects.all()
    serializer_class = RoomTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'capacity', 'is_active']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

@swagger_auto_schema(tags=["Rooms"])
class RoomFacilityViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing room facilities.
    """
    queryset = RoomFacility.objects.all()
    serializer_class = RoomFacilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

@swagger_auto_schema(
    tags=["Rooms"],
    manual_parameters=pagination_params + ordering_params + search_params
)
class RoomViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing rooms.
    """
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['dormitory', 'floor', 'room_type', 'status']
    search_fields = ['room_number', 'description']
    ordering_fields = ['room_number', 'created_at', 'status']

    def get_serializer_class(self):
        if self.action == 'create':
            return RoomCreateSerializer
        return RoomSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Room.objects.none()
            
        user = self.request.user
        if not user.is_authenticated:
            return Room.objects.filter(floor__dormitory__status='active')
            
        if user.is_super_admin:
            return Room.objects.all()
        elif user.is_dormitory_admin:
            return Room.objects.filter(floor__dormitory__admin=user)
        return Room.objects.filter(floor__dormitory__status='active')

@swagger_auto_schema(
    tags=["Bookings"],
    manual_parameters=pagination_params + ordering_params + search_params
)
class RoomBookingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing room bookings.
    """
    queryset = RoomBooking.objects.all()
    serializer_class = RoomBookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['room', 'student', 'status']
    search_fields = ['room__room_number', 'student__user__username']
    ordering_fields = ['created_at', 'status', 'check_in_date']

    def get_serializer_class(self):
        if self.action == 'create':
            return RoomBookingCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RoomBookingUpdateSerializer
        return RoomBookingSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return RoomBooking.objects.none()
            
        user = self.request.user
        if not user.is_authenticated:
            return RoomBooking.objects.none()
            
        if user.is_super_admin:
            return RoomBooking.objects.all()
        elif user.is_dormitory_admin:
            return RoomBooking.objects.filter(room__floor__dormitory__admin=user)
        return RoomBooking.objects.filter(student=user)

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        booking = self.get_object()
        if booking.status == 'Approved':
            room = booking.room
            room.current_occupancy += 1
            # Update room status based on occupancy and capacity
            if room.current_occupancy >= room.room_type.capacity:
                room.status = 'full'
            else:
                room.status = 'partially_filled'
            room.save()
        return response
