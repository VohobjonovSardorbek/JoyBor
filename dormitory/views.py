from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
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
from users.permissions import IsSuperAdmin, IsDormitoryAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@swagger_auto_schema(tags=['University Management'])
class UniversityViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing universities.
    """
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'address']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsSuperAdmin()]
        return [permissions.IsAuthenticated()]


@swagger_auto_schema(tags=['Picture Management'])
class PictureViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing pictures.
    """
    queryset = Picture.objects.all()
    serializer_class = PictureSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsDormitoryAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        dormitory_id = self.request.query_params.get('dormitory_id')
        if dormitory_id:
            return Picture.objects.filter(dormitory_id=dormitory_id)
        return Picture.objects.all()


@swagger_auto_schema(tags=['Dormitory Management'])
class DormitoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing dormitories.
    """
    queryset = Dormitory.objects.all()
    serializer_class = DormitorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'university', 'status']

    def get_serializer_class(self):
        if self.action == 'create':
            return DormitoryCreateSerializer
        return DormitorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsSuperAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.SUPER_ADMIN:
            return Dormitory.objects.all()
        elif user.role == User.DORMITORY_ADMIN:
            return Dormitory.objects.filter(admin=user)
        return Dormitory.objects.filter(status='active')


@swagger_auto_schema(tags=['Floor Management'])
class FloorViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing floors.
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
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsDormitoryAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        dormitory_id = self.request.query_params.get('dormitory_id')
        if dormitory_id:
            return Floor.objects.filter(dormitory_id=dormitory_id)
        return Floor.objects.all()


@swagger_auto_schema(tags=['Room Type Management'])
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
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsSuperAdmin()]
        return [permissions.IsAuthenticated()]


@swagger_auto_schema(tags=['Room Facility Management'])
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
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsSuperAdmin()]
        return [permissions.IsAuthenticated()]


@swagger_auto_schema(tags=['Room Management'])
class RoomViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing rooms.
    """
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['dormitory', 'floor', 'room_type', 'status', 'room_type_category']

    def get_serializer_class(self):
        if self.action == 'create':
            return RoomCreateSerializer
        return RoomSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsDormitoryAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.SUPER_ADMIN:
            return Room.objects.all()
        elif user.role == User.DORMITORY_ADMIN:
            return Room.objects.filter(dormitory__admin=user)
        return Room.objects.filter(status='available')

    @swagger_auto_schema(
        operation_description="Book a room",
        request_body=RoomBookingCreateSerializer,
        responses={
            201: openapi.Response(
                description="Room booked successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'room': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'student': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'start_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                        'end_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    @action(detail=True, methods=['post'])
    def book(self, request, pk=None):
        room = self.get_object()
        if room.status != 'available':
            return Response(
                {'error': 'Room is not available for booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = RoomBookingCreateSerializer(data={
            'room': room.id,
            'student': request.user.id,
            'start_date': request.data.get('start_date'),
            'end_date': request.data.get('end_date'),
            'status': 'Pending'
        })
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(tags=['Room Booking Management'])
class RoomBookingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing room bookings.
    """
    queryset = RoomBooking.objects.all()
    serializer_class = RoomBookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['room', 'student', 'status']

    def get_serializer_class(self):
        if self.action == 'create':
            return RoomBookingCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RoomBookingUpdateSerializer
        return RoomBookingSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsDormitoryAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.SUPER_ADMIN:
            return RoomBooking.objects.all()
        elif user.role == User.DORMITORY_ADMIN:
            return RoomBooking.objects.filter(room__dormitory__admin=user)
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
