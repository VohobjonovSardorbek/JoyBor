from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import *
from .serializers import *
from .models import *
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser


class UserListAPIView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()

        user = self.request.user
        if user.is_superuser:
            return User.objects.all()
        else:
            return User.objects.filter(id=user.id)


class UserCreateAPIView(CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrDormitoryAdmin]
    queryset = User.objects.all()


class UserDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrDormitoryAdmin]

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        if user.is_superuser:
            return User.objects.all()
        else:
            return User.objects.filter(id=user.id)

    def perform_destroy(self, instance):
        if self.request.user.is_superuser:
            raise PermissionDenied("Faqat superadmin foydalanuvchi o'chira oladi")
        instance.delete()


class UniversityListAPIView(ListAPIView):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [AllowAny]


class UniversityCreateAPIView(CreateAPIView):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [IsAdmin]


class UniversityDetailApiView(RetrieveUpdateDestroyAPIView):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [IsAdmin]


class DormitoryListAPIView(ListAPIView):
    queryset = Dormitory.objects.all()
    serializer_class = DormitorySafeSerializer
    permission_classes = [AllowAny]


class DormitoryCreateAPIView(CreateAPIView):
    queryset = Dormitory.objects.all()
    serializer_class = DormitorySerializer
    permission_classes = [IsAdmin]


class DormitoryDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Dormitory.objects.all()
    permission_classes = [IsOwnerOrIsAdmin]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DormitorySafeSerializer
        return DormitorySerializer

    def perform_destroy(self, instance):
        if self.request.user.is_superuser:
            raise PermissionDenied('Faqat superadmin yotoqxona o\'chira oladi')
        instance.delete()


class DormitoryImageListAPIView(ListAPIView):
    serializer_class = DormitoryImageSafeSerializer
    permission_classes = [IsAdminOrDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return DormitoryImage.objects.none()
        user = self.request.user
        if user.is_superuser:
            return DormitoryImage.objects.all()
        elif Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.filter(admin=user)[0]
            return DormitoryImage.objects.filter(dormitory=dormitory)
        return DormitoryImage.objects.none()



class DormitoryImageCreateAPIView(CreateAPIView):
    queryset = DormitoryImage.objects.all()
    serializer_class = DormitoryImageSerializer
    permission_classes = [IsDormitoryAdmin]
    parser_classes = [MultiPartParser, FormParser]


class DormitoryImageDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrDormitoryAdmin]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DormitoryImageSafeSerializer
        return DormitoryImageSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return DormitoryImage.objects.none()
        user = self.request.user
        if user.is_superuser:
            return DormitoryImage.objects.all()
        elif Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.filter(admin=user)[0]
            return DormitoryImage.objects.filter(dormitory=dormitory)
        return DormitoryImage.objects.none()



class FloorListAPIView(ListAPIView):
    serializer_class = FloorSerializer
    permission_classes = [IsAdminOrDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Floor.objects.none()
        user = self.request.user
        if user.is_superuser:
            return Floor.objects.all()
        elif Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            return Floor.objects.filter(dormitory=dormitory)
        return Floor.objects.none()


class FloorCreateAPIView(CreateAPIView):
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer
    permission_classes = [IsDormitoryAdmin]


class FloorDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = FloorSerializer
    permission_classes = [IsAdminOrDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Floor.objects.none()
        user = self.request.user
        if user.is_superuser:
            return Floor.objects.all()
        elif Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            return Floor.objects.filter(dormitory=dormitory)
        return Floor.objects.none()


class RoomListAPIView(ListAPIView):
    serializer_class = RoomSafeSerializer
    permission_classes = [IsAdminOrDormitoryAdmin]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'floor',
                openapi.IN_QUERY,
                description="Floor ID bo‘yicha filterlash",
                type=openapi.TYPE_INTEGER
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Room.objects.none()
        user = self.request.user

        queryset = Room.objects.none()

        if user.is_superuser:
            queryset = Room.objects.all()
        elif Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            floors = Floor.objects.filter(dormitory=dormitory)
            queryset = Room.objects.filter(floor__in=floors)

            floor_id = self.request.query_params.get('floor')
            if floor_id:
                try:
                    floor_id = int(floor_id)
                    if floors.filter(id=floor_id).exists():
                        queryset = queryset.filter(floor_id=floor_id)
                    else:
                        queryset = Room.objects.none()
                except ValueError:
                    queryset = Room.objects.none()

        return queryset


class RoomCreateAPIView(CreateAPIView):
    serializer_class = RoomSerializer
    permission_classes = [IsDormitoryAdmin]
    queryset = Room.objects.all()

    def get_serializer(self, *args, **kwargs):

        if getattr(self, 'swagger_fake_view', False):
            return super().get_serializer(*args, **kwargs)

        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        serializer = serializer_class(*args, **kwargs)

        dormitory = get_object_or_404(Dormitory, admin=self.request.user)
        serializer.fields['floor'].queryset = Floor.objects.filter(dormitory=dormitory)
        return serializer


class RoomDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = RoomSerializer
    permission_classes = [IsAdminOrDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Room.objects.none()
        user = self.request.user
        if user.is_superuser:
            return Room.objects.all()
        elif Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            floors = Floor.objects.filter(dormitory=dormitory)
            return Room.objects.filter(floor__in=floors)
        return Room.objects.none()


class StudentListAPIView(ListAPIView):
    serializer_class = StudentSafeSerializer
    permission_classes = [IsAdminOrDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Student.objects.none()

        user = self.request.user
        if user.is_superuser:
            return Student.objects.all()
        elif Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            return Student.objects.filter(dormitory=dormitory)
        return Student.objects.none()


class StudentCreateAPIView(CreateAPIView):
    serializer_class = StudentSerializer
    permission_classes = [IsDormitoryAdmin]
    queryset = Student.objects.all()
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer(self, *args, **kwargs):

        if getattr(self, 'swagger_fake_view', False):
            return super().get_serializer(*args, **kwargs)

        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        serializer = serializer_class(*args, **kwargs)

        dormitory = get_object_or_404(Dormitory, admin=self.request.user)
        floors = Floor.objects.filter(dormitory=dormitory)

        serializer.fields['floor'].queryset = Floor.objects.filter(dormitory=dormitory)
        serializer.fields['room'].queryset = Room.objects.filter(floor__in=floors)

        province = self.request.data.get('province')
        if province:
            serializer.fields['district'].queryset = District.objects.filter(province=province)
        else:
            serializer.fields['district'].queryset = District.objects.none()

        return serializer


class StudentDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrDormitoryAdmin]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StudentSafeSerializer
        return StudentSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Student.objects.none()

        user = self.request.user
        if user.is_superuser:
            return Student.objects.all()
        elif Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            return Student.objects.filter(dormitory=dormitory)
        return Student.objects.none()

    def perform_destroy(self, instance):
        room = instance.room
        super().perform_destroy(instance)

        room.currentOccupancy = room.students.count()

        if room.currentOccupancy == 0:
            room.status = 'AVAILABLE'
        elif room.currentOccupancy < room.capacity:
            room.status = 'PARTIALLY_OCCUPIED'
        else:
            room.status = 'FULLY_OCCUPIED'

        room.save()


class ApplicationListAPIView(ListAPIView):
    serializer_class = ApplicationSafeSerializer
    permission_classes = [IsAdminOrDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()
        user = self.request.user

        if user.is_superuser:
            return Application.objects.all()

        elif Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            return Application.objects.filter(dormitory=dormitory)
        return Application.objects.none()


class ApplicationCreateAPIView(CreateAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [AllowAny]
    queryset = Application.objects.all()


class ApplicationDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAdminOrDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()
        user = self.request.user

        if user.is_superuser:
            return Application.objects.all()

        elif Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            return Application.objects.filter(dormitory=dormitory)
        return Application.objects.none()


class PaymentListAPIView(ListAPIView):
    serializer_class = PaymentSafeSerializer
    permission_classes = [IsAdminOrDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()
        user = self.request.user

        if user.is_superuser:
            return Payment.objects.all()

        elif Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            return Payment.objects.filter(dormitory=dormitory)
        return Payment.objects.none()


class PaymentCreateAPIView(CreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsDormitoryAdmin]
    queryset = Payment.objects.all()

    def get_serializer(self, *args, **kwargs):

        if getattr(self, 'swagger_fake_view', False):
            return super().get_serializer(*args, **kwargs)


        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        serializer = serializer_class(*args, **kwargs)

        dormitory = get_object_or_404(Dormitory, admin=self.request.user)
        serializer.fields['student'].queryset = Student.objects.filter(dormitory=dormitory)
        return serializer


class PaymentDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminOrDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()
        user = self.request.user

        if user.is_superuser:
            return Payment.objects.all()


        elif Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            return Payment.objects.filter(dormitory=dormitory)
        return Payment.objects.none()


class ProvinceListAPIView(ListAPIView):
    serializer_class = ProvinceSerializer
    queryset = Province.objects.all()
    permission_classes = [AllowAny]


class DistrictListAPIView(ListAPIView):
    serializer_class = DistrictSerializer
    permission_classes = [AllowAny]

    province_param = openapi.Parameter(
        'province', openapi.IN_QUERY,
        description="Filter districts by province ID",
        type=openapi.TYPE_INTEGER,
        required=False
    )

    @swagger_auto_schema(manual_parameters=[province_param])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        province_id = self.request.query_params.get('province')
        if province_id:
            return District.objects.filter(province__id=province_id)
        return District.objects.all()