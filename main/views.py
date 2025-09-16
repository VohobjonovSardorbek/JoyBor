import openpyxl
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import *
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.exceptions import MultipleObjectsReturned
from django.http import Http404
from .permissions import *
from .serializers import *
from .models import *
from rest_framework.exceptions import PermissionDenied, NotFound
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Count, Sum, Q, Prefetch, F, Case, When, IntegerField
from rest_framework.filters import SearchFilter
from rest_framework.parsers import MultiPartParser, FormParser
from .filters import StudentFilter, ApplicationFilter, TaskFilter
from django.utils.dateparse import parse_date
from django.utils.timesince import timesince
from django.utils.timezone import localtime, now, is_naive, make_aware
from django.utils import timezone
from django.db import transaction
from .serializers import UserProfileUpdateSerializer
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests


class GoogleLoginAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=GoogleLoginSerializer,
                         operation_description="Login with Google and receive JWT access & refresh tokens",
                         responses={200: "JWT tokens and user info"})
    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']

        try:
            # Google ID token tekshirish
            client_id = settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id']
            if not client_id:
                return Response({"error": "Google Client ID not configured"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), client_id
            )

            # Token muddati tekshirish
            if idinfo['exp'] < timezone.now().timestamp():
                return Response({"error": "Token expired"}, status=status.HTTP_400_BAD_REQUEST)

            email = idinfo.get('email')
            if not email:
                return Response({"error": "Email not found in token"}, status=status.HTTP_400_BAD_REQUEST)

            # Foydalanuvchi yaratish yoki topish
            username = email.split('@')[0]
            # Username konfliktini oldini olish
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': username,
                    'role': 'student',
                    'first_name': idinfo.get('given_name', ''),
                    'last_name': idinfo.get('family_name', '')
                }
            )

            # Agar foydalanuvchi allaqachon mavjud bo'lsa, ma'lumotlarni yangilash
            if not created:
                user.first_name = idinfo.get('given_name', user.first_name)
                user.last_name = idinfo.get('family_name', user.last_name)
                user.save()

            # UserProfile yaratish
            profile, profile_created = UserProfile.objects.get_or_create(user=user)

            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'role': user.role,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_new_user': created
            })

        except ValueError as e:
            return Response({"error": f"Invalid Google token: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Authentication failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


class UserProfileView(RetrieveUpdateAPIView):
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=ChangePasswordSerializer)
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        user = request.user

        if serializer.is_valid():
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({"old_password": "Eski parol noto'g'ri!"}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"detail": "Parol muvaffaqiyatli o'zgartirildi!"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentRegisterCreateAPIView(CreateAPIView):
    serializer_class = StudentRegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = User.objects.get(username=response.data['username'])
        refresh = RefreshToken.for_user(user)
        response.data['refresh'] = str(refresh)
        response.data['access'] = str(refresh.access_token)
        return response


class TenantRegisterAPIView(CreateAPIView):
    serializer_class = TenantRegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = User.objects.get(username=response.data['username'])
        refresh = RefreshToken.for_user(user)
        response.data['refresh'] = str(refresh)
        response.data['access'] = str(refresh.access_token)
        return response


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
        if not self.request.user.is_superuser:
            raise PermissionDenied("Faqat superadmin foydalanuvchi o'chira oladi")
        instance.delete()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


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


class MyDormitoryAPIView(RetrieveAPIView):
    permission_classes = [IsDormitoryAdmin]
    serializer_class = DormitorySafeSerializer

    def get_object(self):
        return get_object_or_404(Dormitory, admin=self.request.user)


class MyDormitoryUpdateAPIView(UpdateAPIView):
    permission_classes = [IsDormitoryAdmin]
    serializer_class = MyDormitorySerializer

    def get_object(self):
        return get_object_or_404(Dormitory, admin=self.request.user)


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
        if not self.request.user.is_superuser:
            raise PermissionDenied('Faqat superadmin yotoqxona o\'chira oladi')
        instance.delete()


class DormitoryImageListAPIView(ListAPIView):
    serializer_class = DormitoryImageSafeSerializer
    permission_classes = [IsDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return DormitoryImage.objects.none()
        user = self.request.user
        if user.is_superuser:
            return DormitoryImage.objects.all()
        try:
            dormitory = Dormitory.objects.get(admin=user)
            return DormitoryImage.objects.filter(dormitory=dormitory)
        except Dormitory.DoesNotExist:
            return DormitoryImage.objects.none()


class DormitoryImageCreateAPIView(CreateAPIView):
    queryset = DormitoryImage.objects.all()
    serializer_class = DormitoryImageSerializer
    permission_classes = [IsDormitoryAdmin]
    parser_classes = [MultiPartParser, FormParser]


class DormitoryImageDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsDormitoryAdmin]

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
        try:
            dormitory = Dormitory.objects.get(admin=user)
            return DormitoryImage.objects.filter(dormitory=dormitory)
        except Dormitory.DoesNotExist:
            return DormitoryImage.objects.none()


class FloorListAPIView(ListAPIView):
    serializer_class = FloorSerializer
    permission_classes = [IsDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Floor.objects.none()
        user = self.request.user
        if Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            return Floor.objects.filter(dormitory=dormitory)
        return Floor.objects.none()


class FloorCreateAPIView(CreateAPIView):
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer
    permission_classes = [IsDormitoryAdmin]


class FloorDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = FloorSerializer
    permission_classes = [IsDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Floor.objects.none()
        user = self.request.user
        if Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            return Floor.objects.filter(dormitory=dormitory)
        return Floor.objects.none()


class RoomListAPIView(ListAPIView):
    serializer_class = RoomSafeSerializer
    permission_classes = [IsDormitoryAdmin]

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
        dormitory = Dormitory.objects.get(admin=user)
        queryset = Room.objects.filter(floor__dormitory=dormitory)

        floor_id = self.request.query_params.get('floor')
        if floor_id and floor_id.isdigit():
            queryset = queryset.filter(floor_id=int(floor_id))
        elif floor_id:
            return Room.objects.none()

        return queryset


class EveryAvailableRoomsAPIView(ListAPIView):
    serializer_class = RoomSerializer

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

        dormitory = get_object_or_404(Dormitory, admin=self.request.user)
        floors = Floor.objects.filter(dormitory=dormitory)
        rooms = Room.objects.filter(floor__in=floors).exclude(status='FULLY_OCCUPIED')

        floor_id = self.request.query_params.get('floor')
        if floor_id and floor_id.isdigit():
            rooms = rooms.filter(floor_id=int(floor_id))

        return rooms


class AvailableFloorsAPIView(ListAPIView):
    serializer_class = FloorSerializer

    def get_queryset(self):
        dormitory = get_object_or_404(Dormitory, admin=self.request.user)
        return Floor.objects.filter(dormitory=dormitory)


class AvailableRoomsAPIView(ListAPIView):
    serializer_class = RoomSerializer

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

        dormitory = Dormitory.objects.filter(admin=user).first()
        if not dormitory:
            return queryset

        floors = Floor.objects.filter(dormitory=dormitory)
        queryset = Room.objects.filter(floor__in=floors).exclude(status='FULLY_OCCUPIED')

        floor_id = self.request.query_params.get('floor')
        if floor_id and floor_id.isdigit():
            floor_id = int(floor_id)
            if floors.filter(id=floor_id).exists():
                queryset = queryset.filter(floor_id=floor_id)
            else:
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
    permission_classes = [IsDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Room.objects.none()
        user = self.request.user
        if Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            floors = Floor.objects.filter(dormitory=dormitory)
            return Room.objects.filter(floor__in=floors)
        return Room.objects.none()


# Status constants
STATUS_APPROVED = 'APPROVED'
STATUS_QABUL = 'Qabul qilindi'
STATUS_TEKSHIRMAYDI = 'Tekshirilmaydi'
STATUS_QARZDOR = 'Qarzdor'
STATUS_HAQDOR = 'Haqdor'


def update_students_status_for_user(user):
    today = timezone.now().date()

    dormitory = Dormitory.objects.filter(admin=user).first()
    if not dormitory:
        return

    approved_payments_qs = (
        Payment.objects.filter(status=STATUS_APPROVED)
        .order_by('-valid_until')
    )

    students = (
        Student.objects.filter(dormitory=dormitory)
        .prefetch_related(
            Prefetch('payments', queryset=approved_payments_qs, to_attr='approved_payments')
        )
    )

    for student in students:
        if student.placement_status == STATUS_QABUL:
            new_status = STATUS_TEKSHIRMAYDI
        else:
            last_payment = student.approved_payments[0] if student.approved_payments else None
            if not last_payment or not last_payment.valid_until or last_payment.valid_until < today:
                new_status = STATUS_QARZDOR
            else:
                new_status = STATUS_HAQDOR

        if student.status != new_status:
            student.status = new_status
            student.save(update_fields=['status'])


filter_params = [
    openapi.Parameter('name', openapi.IN_QUERY, description="Talaba ismi bo'yicha qidiruv", type=openapi.TYPE_STRING),
    openapi.Parameter('last_name', openapi.IN_QUERY, description="Talaba familiyasi bo'yicha qidiruv",
                      type=openapi.TYPE_STRING),
    openapi.Parameter('floor_id', openapi.IN_QUERY, description="Qavat bo'yicha filter", type=openapi.TYPE_INTEGER),
    openapi.Parameter('status', openapi.IN_QUERY, description="Status bo'yicha filter", type=openapi.TYPE_STRING,
                      enum=['Qarzdor', 'Haqdor', 'Tekshirilmaydi']),
    openapi.Parameter('placement_status', openapi.IN_QUERY, description="Joylashish holati bo'yicha filter",
                      type=openapi.TYPE_STRING, enum=['Qabul qilindi', 'Joylashdi']),
    openapi.Parameter('max_payment', openapi.IN_QUERY, description="To'lov summasi (kamroq)",
                      type=openapi.TYPE_INTEGER),
]


class StudentListAPIView(ListAPIView):
    serializer_class = StudentSafeSerializer
    permission_classes = [IsDormitoryAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = StudentFilter
    search_fields = ['name', 'last_name']

    @swagger_auto_schema(manual_parameters=filter_params)
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Student.objects.none()

        user = self.request.user

        update_students_status_for_user(user)

        dormitory = Dormitory.objects.filter(admin=user).first()
        return Student.objects.filter(dormitory=dormitory) if dormitory else Student.objects.none()


class ExportStudentExcelAPIView(APIView):
    permission_classes = [IsDormitoryAdmin]

    def get(self, request, *args, **kwargs):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Talabalar"

        # O'zbekcha ustun nomlari
        ws.append([
            '№',
            'Ism',
            'Familiya',
            'Otasining ismi',
            'Viloyat',
            'Tuman',
            'Fakultet',
            'Yo‘nalish',
            'Guruh',
            'Kurs',
            'Jinsi',
            'Telefon',
            'Pasport',
            'Imtiyoz',
            'Holati',
            'Qabul qilingan sana'
        ])

        dormitory = get_object_or_404(Dormitory, admin=request.user)
        students = Student.objects.select_related('province', 'district').filter(dormitory=dormitory)

        # 1 dan boshlab tartib raqamini qo'shish
        for index, student in enumerate(students, start=1):
            ws.append([
                index,  # student.id o‘rniga oddiy tartib raqami
                student.name,
                student.last_name or '',
                student.middle_name or '',
                student.province.name if student.province else '',
                student.district.name if student.district else '',
                student.faculty or '',
                student.direction or '',
                student.group or '',
                student.course or '',
                student.gender or '',
                student.phone or '',
                student.passport or '',
                'Ha' if student.privilege else 'Yo‘q',
                student.status or '',
                student.accepted_date.strftime('%Y-%m-%d') if student.accepted_date else ''
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=talabalar.xlsx'
        wb.save(response)
        return response


ROOM_STATUS_AVAILABLE = 'AVAILABLE'
ROOM_STATUS_PARTIALLY = 'PARTIALLY_OCCUPIED'
ROOM_STATUS_FULL = 'FULLY_OCCUPIED'

PLACEMENT_STATUS_DONE = 'Joylashdi'


def _get_dormitory_for_user_or_404(user):
    try:
        return Dormitory.objects.get(admin=user)
    except Dormitory.DoesNotExist:
        raise Http404("Dormitory not found for this user.")
    except MultipleObjectsReturned:
        return Dormitory.objects.filter(admin=user).first()


class StudentCreateAPIView(CreateAPIView):
    serializer_class = StudentSerializer
    permission_classes = [IsDormitoryAdmin]
    queryset = Student.objects.all()
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer(self, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            return super().get_serializer(*args, **kwargs)

        serializer = super().get_serializer(*args, **kwargs)

        dormitory = _get_dormitory_for_user_or_404(self.request.user)

        floors_qs = Floor.objects.filter(dormitory=dormitory)
        rooms_qs = Room.objects.filter(floor__in=floors_qs).exclude(status=ROOM_STATUS_FULL)

        if 'floor' in serializer.fields:
            serializer.fields['floor'].queryset = floors_qs
        if 'room' in serializer.fields:
            serializer.fields['room'].queryset = rooms_qs

        province = self.request.data.get('province') or self.request.query_params.get('province')
        if 'district' in serializer.fields:
            if province:
                serializer.fields['district'].queryset = District.objects.filter(province_id=province)
            else:
                serializer.fields['district'].queryset = District.objects.none()

        return serializer


class StudentDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsDormitoryAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StudentSafeSerializer
        return StudentSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Student.objects.none()

        update_students_status_for_user(self.request.user)

        try:
            dormitory = Dormitory.objects.get(admin=self.request.user)
        except Dormitory.DoesNotExist:
            return Student.objects.none()
        except MultipleObjectsReturned:
            dormitory = Dormitory.objects.filter(admin=self.request.user).first()
            if not dormitory:
                return Student.objects.none()

        return Student.objects.filter(dormitory=dormitory).select_related('room', 'floor')

    def perform_destroy(self, instance):
        room = instance.room

        with transaction.atomic():
            super().perform_destroy(instance)

            new_occupancy = room.students.count()
            room.currentOccupancy = new_occupancy

            if new_occupancy == 0:
                room.status = ROOM_STATUS_AVAILABLE
            elif new_occupancy < room.capacity:
                room.status = ROOM_STATUS_PARTIALLY
            else:
                room.status = ROOM_STATUS_FULL

            room.save(update_fields=['currentOccupancy', 'status'])

    def perform_update(self, serializer):
        with transaction.atomic():
            instance = serializer.save()

            if getattr(instance, 'floor', None) and getattr(instance, 'room', None):
                if instance.placement_status != PLACEMENT_STATUS_DONE:
                    Student.objects.filter(pk=instance.pk).update(placement_status=PLACEMENT_STATUS_DONE)
                    instance.placement_status = PLACEMENT_STATUS_DONE


class ApplicationListAPIView(ListAPIView):
    serializer_class = ApplicationSafeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ApplicationFilter

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()
        user = self.request.user

        if Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            return Application.objects.filter(dormitory=dormitory)
        else:
            return Application.objects.filter(user=user)


class ApplicationCreateAPIView(CreateAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]
    queryset = Application.objects.all()
    parser_classes = [MultiPartParser, FormParser]


class ApplicationDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.request.method in ['PATCH', 'PUT']:
            return ApplicationSerializer
        return ApplicationSafeSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()
        user = self.request.user

        if Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            return Application.objects.filter(dormitory=dormitory)
        else:
            return Application.objects.filter(user=user)


class PaymentListAPIView(ListAPIView):
    serializer_class = PaymentSafeSerializer
    permission_classes = [IsDormitoryAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['student__name']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Payment.objects.none()
        user = self.request.user

        if not Dormitory.objects.filter(admin=user).exists():
            return Payment.objects.none()

        dormitory = Dormitory.objects.get(admin=user)
        queryset = Payment.objects.filter(dormitory=dormitory)

        at_date = self.request.query_params.get('date')
        if at_date:
            parsed_date = parse_date(at_date)
            if parsed_date:
                queryset = queryset.filter(paid_date=parsed_date)

        return queryset


class ExportPaymentExcelAPIView(APIView):
    permission_classes = [IsDormitoryAdmin]

    def get(self, request, *args, **kwargs):
        dormitory = get_object_or_404(Dormitory, admin=request.user)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "To'lovlar"

        ws.append([
            '№',
            'Talaba ismi',
            'Familiya',
            'Kurs',
            'Xona',
            'Miqdori',
            'To‘langan sana',
            'Amal qilish muddati',
            'To‘lov usuli',
            'Holati',
            'Izoh'
        ])

        payments = Payment.objects.select_related('student', 'student__room').filter(dormitory=dormitory)

        for index, payment in enumerate(payments, start=1):
            ws.append([
                index,  # payment.id o‘rniga oddiy tartib raqami
                payment.student.name,
                payment.student.last_name or '',
                payment.student.course or '',
                payment.student.room.name if payment.student.room else '',
                payment.amount,
                payment.paid_date.strftime('%Y-%m-%d %H:%M') if payment.paid_date else '',
                payment.valid_until.strftime('%Y-%m-%d') if payment.valid_until else '',
                payment.method,
                payment.status,
                payment.comment or ''
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=tolovlar.xlsx'
        wb.save(response)
        return response


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
    permission_classes = [IsDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()
        user = self.request.user

        if Dormitory.objects.filter(admin=user).exists():
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


class AdminDashboardAPIView(APIView):
    permission_classes = [IsDormitoryAdmin]

    def get(self, request):
        dormitory = Dormitory.objects.filter(admin=request.user).first()
        if not dormitory:
            return Response({"detail": "Dormitory not found"}, status=404)

        students_stats = Student.objects.filter(dormitory=dormitory).aggregate(
            total=Count('id'),
            male=Count('id', filter=Q(gender='Erkak')),
            female=Count('id', filter=Q(gender='Ayol')),
        )

        rooms_qs = Room.objects.filter(floor__dormitory=dormitory)
        rooms_stats = rooms_qs.aggregate(
            available_places_total=Sum(F('capacity') - F('currentOccupancy')),
            available_places_male=Sum(
                Case(
                    When(gender='male', then=F('capacity') - F('currentOccupancy')),
                    default=0,
                    output_field=IntegerField()
                )
            ),
            available_places_female=Sum(
                Case(
                    When(gender='female', then=F('capacity') - F('currentOccupancy')),
                    default=0,
                    output_field=IntegerField()
                )
            ),
        )

        payments = Payment.objects.filter(dormitory=dormitory, status='APPROVED')
        payment_stats = payments.aggregate(
            total_payment=Sum('amount')
        )

        debtor_students = Student.objects.filter(dormitory=dormitory, status='Qarzdor').count()
        non_debtor_students = Student.objects.filter(dormitory=dormitory, status='Haqdor').count()
        unplaced_student = Student.objects.filter(dormitory=dormitory, status='Tekshirilmaydi').count()

        applications = Application.objects.filter(dormitory=dormitory)
        application_stats = applications.aggregate(
            total=Count('id'),
            approved=Count('id', filter=Q(status='APPROVED')),
            rejected=Count('id', filter=Q(status='REJECTED')),
        )
        recent_applications = applications.order_by('-created_at')[:10]

        data = {
            "students": students_stats,
            "rooms": {
                "available_places_total": rooms_stats['available_places_total'] or 0,
                "available_places_male": rooms_stats['available_places_male'] or 0,
                "available_places_female": rooms_stats['available_places_female'] or 0,
            },
            "payments": {
                "debtor_students_count": debtor_students,
                "non_debtor_students_count": non_debtor_students,
                "unplaced_students_count": unplaced_student,
                "total_payment": payment_stats['total_payment'] or 0,
            },
            "applications": application_stats,
            "recent_applications": RecentApplicationSerializer(recent_applications, many=True).data
        }

        return Response(data)


class MonthlyRevenueAPIView(APIView):
    permission_classes = [IsDormitoryAdmin]

    def get(self, request):
        user = request.user
        data = MonthlyRevenueSerializer.get_monthly_revenue_for_user(user)
        return Response(data)


class RoomStatusStatsAPIView(APIView):
    permission_classes = [IsDormitoryAdmin]

    def get(self, request):
        user = request.user

        rooms = Room.objects.filter(floor__dormitory__admin=user)

        available = rooms.filter(status='AVAILABLE').count()
        partially = rooms.filter(status='PARTIALLY_OCCUPIED').count()
        fully = rooms.filter(status='FULLY_OCCUPIED').count()

        return Response({
            'available': available,
            'partially_occupied': partially,
            'fully_occupied': fully
        })


class TasksListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsDormitoryAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TaskSafeSerializer
        return TaskSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Task.objects.none()

        user = self.request.user
        return Task.objects.filter(user=user).order_by('-created_at')


class TaskDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsDormitoryAdmin]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TaskSafeSerializer
        return TaskSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Task.objects.none()

        user = self.request.user
        return Task.objects.filter(user=user).order_by('-created_at')


class RecentActivityAPIView(APIView):
    permission_classes = [IsDormitoryAdmin]

    def get(self, request):
        user = request.user
        dormitory = Dormitory.objects.filter(admin=user).first()
        if not dormitory:
            return Response({"detail": "Dormitory not found"}, status=404)

        activities = []

        payments = Payment.objects.filter(
            dormitory=dormitory, status='APPROVED'
        ).order_by('-paid_date')[:15]
        for payment in payments:
            paid_date = payment.paid_date
            if is_naive(paid_date):
                paid_date = make_aware(paid_date)
            activities.append({
                "type": "payment_approved",
                "title": "To‘lov tasdiqlandi",
                "desc": f"{payment.student.name} - {payment.amount:,} so'm",
                "time": timesince(localtime(paid_date), now()) + " ago",
                "datetime": paid_date,
            })

        applications = Application.objects.filter(
            dormitory=dormitory
        ).order_by('-created_at')[:15]
        for application in applications:
            created_at = application.created_at
            if is_naive(created_at):
                created_at = make_aware(created_at)
            activities.append({
                "type": "new_application",
                "title": "Yangi ariza",
                "desc": f"{application.name} - {application.comment or ''}",
                "time": timesince(localtime(created_at), now()) + " ago",
                "datetime": created_at,
            })

        debtors = Student.objects.filter(
            dormitory=dormitory,
            status='Qarzdor'
        ).order_by('-accepted_date')[:15]
        for debtor in debtors:
            accepted_date = debtor.accepted_date
            if is_naive(accepted_date):
                accepted_date = make_aware(accepted_date)
            activities.append({
                "type": "debt",
                "title": "To‘lov kechikishi",
                "desc": f"{debtor.name} - {debtor.course}",
                "time": timesince(localtime(accepted_date), now()) + " ago",
                "datetime": accepted_date,
            })

        students = Student.objects.filter(dormitory=dormitory).order_by('-accepted_date')[:15]
        for student in students:
            accepted_date = student.accepted_date
            if is_naive(accepted_date):
                accepted_date = make_aware(accepted_date)
            activities.append({
                "type": "new_student",
                "title": "Yangi talaba qo‘shildi",
                "desc": f"{student.name} - {student.course}",
                "time": timesince(localtime(accepted_date), now()) + " ago",
                "datetime": accepted_date,
            })

        activities = sorted(activities, key=lambda x: x['datetime'], reverse=True)[:15]

        for act in activities:
            act.pop('datetime', None)

        return Response({"activities": activities})


class ApartmentListAPIView(ListAPIView):
    queryset = Apartment.objects.all()
    serializer_class = ApartmentSafeSerializer
    permission_classes = [AllowAny]


class MyApartmentListAPIView(ListAPIView):
    serializer_class = ApartmentSafeSerializer
    permission_classes = [IsIjarachiAdmin]

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated:
            return Apartment.objects.filter(user=user)
        return Apartment.objects.none()


class ApartmentDetailAPIView(RetrieveAPIView):
    queryset = Apartment.objects.all()
    serializer_class = ApartmentSafeSerializer
    permission_classes = [AllowAny]


class ApartmentCreateAPIView(CreateAPIView):
    serializer_class = ApartmentSerializer
    permission_classes = [IsIjarachiAdmin, IsAdmin]


class ApartmentUpdateAPIView(UpdateAPIView):
    queryset = Apartment.objects.all()
    serializer_class = ApartmentSerializer
    permission_classes = [IsIjarachiAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()
        user = self.request.user
        return Apartment.objects.filter(user=user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class AmenityUpdateAPIView(UpdateAPIView):
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    permission_classes = [IsAdminOrDormitoryAdmin]


class RuleListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Rule.objects.none()

        if not self.request.user.is_authenticated:
            return Rule.objects.none()
        return Rule.objects.filter(dormitory__admin=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RuleCreateSerializer
        return RuleSafeSerializer

    def perform_create(self, serializer):
        dormitory = Dormitory.objects.filter(admin=self.request.user).first()
        if not dormitory:
            raise PermissionDenied("Siz hech qanday yotoqxona admini emassiz.")
        serializer.save(dormitory=dormitory)


class RuleRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsDormitoryAdmin]
    serializer_class = RuleSafeSerializer  # default serializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Rule.objects.none()

        if not self.request.user.is_authenticated:
            return Rule.objects.none()
        return Rule.objects.filter(dormitory__admin=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return RuleCreateSerializer
        return RuleSafeSerializer


class AmenityListAPIView(ListAPIView):
    serializer_class = AmenitySerializer
    permission_classes = [IsAuthenticated]
    queryset = Amenity.objects.all()


class ApartmentImageListCreateAPIView(ListCreateAPIView):
    serializer_class = ApartmentImageSerializer
    permission_classes = [IsIjarachiAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ApartmentImage.objects.none()

        if not self.request.user.is_authenticated:
            return ApartmentImage.objects.none()
        return ApartmentImage.objects.filter(apartment__user=self.request.user)

    def perform_create(self, serializer):
        apartment = serializer.validated_data.get('apartment')

        if apartment.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Siz faqat o'zingizga tegishli apartment uchun rasm qo'shishingiz mumkin.")

        serializer.save()


class ApartmentImageDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = ApartmentImageSerializer
    permission_classes = [IsIjarachiAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ApartmentImage.objects.none()

        if not self.request.user.is_authenticated:
            return ApartmentImage.objects.none()
        return ApartmentImage.objects.filter(apartment__user=self.request.user)


#
# class NotificationCreateView(CreateAPIView):
#     serializer_class = NotificationCreateSerializer
#     permission_classes = [IsAdmin]
#     parser_classes = [MultiPartParser, FormParser]
#
#     def perform_create(self, serializer):
#         notification = serializer.save()
#
#         # Foydalanuvchilarni aniqlash va bildirishnoma yuborish
#         target_type = notification.target_type
#
#         if target_type == 'all_students':
#             users = User.objects.filter(role='student')
#         elif target_type == 'all_admins':
#             users = User.objects.filter(role='admin')
#         elif target_type == 'specific_user':
#             users = [notification.target_user] if notification.target_user else []
#         else:
#             users = []
#
#         # UserNotification yaratish
#         user_notifications = []
#         for user in users:
#             user_notifications.append(
#                 UserNotification(user=user, notification=notification)
#             )
#
#         UserNotification.objects.bulk_create(user_notifications, ignore_conflicts=True)
#
#         return notification

#
# class NotificationListView(ListAPIView):
#     serializer_class = NotificationSerializer
#     permission_classes = [IsAuthenticated]
#
#     def get_queryset(self):
#         user = self.request.user
#
#         if not user.is_authenticated:
#             return Notification.objects.none()
#
#         if user.is_superuser:
#             # Superadmin barcha bildirishnomalarni ko'radi
#             return Notification.objects.filter(is_active=True)
#         else:
#             # Oddiy foydalanuvchilar faqat o'zlariga yuborilganlarni ko'radi
#             return Notification.objects.filter(
#                 recipients__user=user,
#                 is_active=True
#             )


class UserNotificationListView(ListAPIView):
    serializer_class = UserNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return UserNotification.objects.filter(
            user=self.request.user,
            notification__is_active=True
        )

    def list(self, request, *args, **kwargs):
        # System notificationlar (UserNotification)
        system_qs = self.get_queryset().select_related('notification')
        system_items = []
        for un in system_qs:
            system_items.append({
                'id': un.id,
                'message': un.notification.message,
                'image_url': NotificationSerializer(un.notification, context={'request': request}).data.get(
                    'image_url'),
                'is_read': un.is_read,
                'created_at': un.notification.created_at,
            })

        # Application notificationlar
        app_qs = ApplicationNotification.objects.filter(user=request.user)
        app_items = []
        for an in app_qs:
            app_items.append({
                'id': an.id,
                'message': an.message,
                'image_url': None,
                'is_read': an.is_read,
                'created_at': an.created_at,
            })

        combined = system_items + app_items
        combined.sort(key=lambda x: x['created_at'], reverse=True)

        # Sana formatlash
        for item in combined:
            if item['created_at']:
                item['created_at'] = localtime(item['created_at']).strftime('%Y-%m-%d %H:%M:%S')

        return Response({'notifications': combined})


class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=MarkNotificationReadSerializer,
        responses={
            200: openapi.Response(
                description="Bildirishnoma muvaffaqiyatli o‘qilgan deb belgilandi",
                examples={
                    "application/json": {"detail": "Bildirishnoma o'qildi deb belgilandi"}
                }
            ),
            404: openapi.Response(
                description="Bildirishnoma topilmadi",
                examples={
                    "application/json": {"error": "Bildirishnoma topilmadi"}
                }
            ),
            400: openapi.Response(
                description="Notog‘ri ma’lumot yuborilgan",
                examples={
                    "application/json": {"notification_id": ["Ushbu maydon to‘ldirilishi shart."]}
                }
            ),
        }
    )
    def post(self, request):
        serializer = MarkNotificationReadSerializer(data=request.data)
        if serializer.is_valid():
            notification_id = serializer.validated_data['notification_id']

            try:
                user_notification = UserNotification.objects.get(
                    user=request.user,
                    notification_id=notification_id
                )
                user_notification.is_read = True
                user_notification.save()

                return Response({'detail': 'Bildirishnoma o\'qildi deb belgilandi'})
            except UserNotification.DoesNotExist:
                return Response(
                    {'error': 'Bildirishnoma topilmadi'},
                    status=status.HTTP_404_NOT_FOUND
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationDetailView(RetrieveAPIView):
    serializer_class = UserNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserNotification.objects.none()

        return UserNotification.objects.filter(
            user=self.request.user,
            notification__is_active=True
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if not instance.is_read:
            instance.is_read = True
            instance.save(update_fields=["is_read"])

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class UnreadNotificationCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        system_unread = UserNotification.objects.filter(
            user=request.user,
            is_read=False,
            notification__is_active=True
        ).count()
        application_unread = ApplicationNotification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        return Response({'unread_count': system_unread + application_unread})


class NotificationsMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Barcha (system + application) bildirishnomalarni o'qildi deb belgilash",
        responses={
            200: openapi.Response(
                description="Muvaffaqiyatli barchasi o'qildi deb belgilandi",
                examples={
                    "application/json": {
                        "detail": "Barcha bildirishnomalar o'qildi deb belgilandi",
                        "updated_system": 3,
                        "updated_application": 2
                    }
                }
            )
        }
    )
    def post(self, request):
        updated_system = UserNotification.objects.filter(
            user=request.user,
            is_read=False,
            notification__is_active=True
        ).update(is_read=True)

        updated_application = ApplicationNotification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)

        return Response({
            'detail': 'Barcha bildirishnomalar o\'qildi deb belgilandi',
            'updated_system': updated_system,
            'updated_application': updated_application
        })


class StatisticsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        data = {
            'students_count': Student.objects.count(),
            'dormitories_count': Dormitory.objects.count(),
            'apartments_count': Apartment.objects.count(),
        }
        return Response(data)


class ApplicationNotificationRetrieveAPIView(RetrieveAPIView):
    serializer_class = ApplicationNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return ApplicationNotification.objects.none()
        return ApplicationNotification.objects.filter(user=user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if not instance.is_read:
            instance.is_read = True
            instance.save(update_fields=["is_read"])

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ApplicationNotificationMarkAsReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ApplicationNotificationReadSerializer,
        operation_description="Application notification ni o'qildi deb belgilash (faqat notification_id yuborish kerak)",
        responses={
            200: openapi.Response(
                description="Muvaffaqiyatli o'qildi deb belgilandi",
                examples={
                    "application/json": {
                        "detail": "Bildirishnoma o'qildi deb belgilandi",
                        "notification_id": 1
                    }
                }
            ),
            404: openapi.Response(
                description="Bildirishnoma topilmadi",
                examples={
                    "application/json": {
                        "error": "Bildirishnoma topilmadi"
                    }
                }
            ),
            400: openapi.Response(
                description="Xato ma'lumotlar",
                examples={
                    "application/json": {
                        "notification_id": ["Bu maydon majburiy"]
                    }
                }
            )
        }
    )
    def post(self, request):
        serializer = ApplicationNotificationReadSerializer(data=request.data)
        if serializer.is_valid():
            notification_id = serializer.validated_data['notification_id']

            try:
                notification = ApplicationNotification.objects.get(
                    id=notification_id,
                    user=request.user
                )
                notification.is_read = True
                notification.save(update_fields=['is_read'])

                return Response({
                    'detail': 'Bildirishnoma o\'qildi deb belgilandi',
                    'notification_id': notification_id
                })
            except ApplicationNotification.DoesNotExist:
                return Response(
                    {'error': 'Bildirishnoma topilmadi'},
                    status=status.HTTP_404_NOT_FOUND
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LikeToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=LikeCreateSerializer,
        operation_description="Dormitory yoki Apartment ga like qo'yish yoki olib tashlash",
        responses={
            200: openapi.Response(
                description="Like muvaffaqiyatli qo'shildi yoki olib tashlandi",
                examples={
                    "application/json": {
                        "detail": "Like qo'shildi",
                        "is_liked": True,
                        "like_id": 1
                    }
                }
            ),
            400: openapi.Response(
                description="Xato ma'lumotlar",
                examples={
                    "application/json": {
                        "error": "Ma'lumotlar noto'g'ri"
                    }
                }
            )
        }
    )
    def post(self, request):
        serializer = LikeCreateSerializer(data=request.data)
        if serializer.is_valid():
            content_type = serializer.validated_data['content_type']
            object_id = serializer.validated_data['object_id']

            # Like mavjudligini tekshirish
            existing_like = Like.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=object_id
            ).first()

            if existing_like:
                # Like mavjud bo'lsa, uni o'chirish
                existing_like.delete()
                return Response({
                    'detail': 'Like olib tashlandi',
                    'is_liked': False,
                    'like_id': None
                })
            else:
                # Like mavjud bo'lmasa, qo'shish
                like = Like.objects.create(
                    user=request.user,
                    content_type=content_type,
                    object_id=object_id
                )
                return Response({
                    'detail': 'Like qo\'shildi',
                    'is_liked': True,
                    'like_id': like.id
                })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LikeStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Dormitory yoki Apartment ning like holatini tekshirish",
        manual_parameters=[
            openapi.Parameter(
                'content_type',
                openapi.IN_QUERY,
                description="Content type (dormitory yoki apartment)",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'object_id',
                openapi.IN_QUERY,
                description="Object ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Like holati",
                examples={
                    "application/json": {
                        "is_liked": True,
                        "total_likes": 15
                    }
                }
            )
        }
    )
    def get(self, request):
        content_type = request.query_params.get('content_type')
        object_id = request.query_params.get('object_id')

        if not content_type or not object_id:
            return Response(
                {'error': 'content_type va object_id kerak'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            object_id = int(object_id)
        except ValueError:
            return Response(
                {'error': 'object_id raqam bo\'lishi kerak'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Foydalanuvchining like qo'yganligini tekshirish
        is_liked = Like.objects.filter(
            user=request.user,
            content_type=content_type,
            object_id=object_id
        ).exists()

        # Umumiy like sonini hisoblash
        total_likes = Like.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).count()

        return Response({
            'is_liked': is_liked,
            'total_likes': total_likes
        })


class UserLikesAPIView(ListAPIView):
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Foydalanuvchining barcha like lari",
        manual_parameters=[
            openapi.Parameter(
                'content_type',
                openapi.IN_QUERY,
                description="Content type filter (dormitory yoki apartment)",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="Foydalanuvchining like lari",
                examples={
                    "application/json": {
                        "id": 1,
                        "content_type": "dormitory",
                        "object_id": 5,
                        "created_at": "2024-01-15T10:30:00Z",
                        "dormitory_data": {
                            "id": 5,
                            "name": "Yotoqxona nomi",
                            "address": "Manzil",
                            "description": "Tavsif",
                            "month_price": 500000,
                            "year_price": 5000000,
                            "distance_to_university": 2.5,
                            "is_active": True,
                            "university_name": "Universitet nomi",
                            "admin_username": "admin_username",
                            "amenities": ["WiFi", "Konditsioner"],
                            "total_students": 150,
                            "approved_applications": 25
                        },
                        "apartment_data": None
                    }
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Like.objects.filter(user=self.request.user).select_related('user')
        content_type = self.request.query_params.get('content_type')

        if content_type:
            queryset = queryset.filter(content_type=content_type)

        return queryset.order_by('-created_at')


class AttendanceSessionListAPIView(ListAPIView):
    serializer_class = AttendanceSessionSafeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == 'admin' and hasattr(user, "dormitory") and user.dormitory:
            return AttendanceSession.objects.filter(
                floor__dormitory__admin=user
            )

        elif user.role == 'floor_leader':
            if hasattr(user, "floor_leader") and user.floor_leader.floor:
                return AttendanceSession.objects.filter(
                    floor=user.floor_leader.floor
                )
            return AttendanceSession.objects.none()

        return AttendanceSession.objects.none()


class AttendanceSessionCreateAPIView(CreateAPIView):
    serializer_class = AttendanceSessionSerializer
    permission_classes = [IsFloorLeader]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AttendanceSession.objects.none()
        try:
            leader = FloorLeader.objects.get(user=self.request.user)
        except FloorLeader.DoesNotExist:
            return AttendanceSession.objects.none()
        return AttendanceSession.objects.filter(floor=leader.floor).prefetch_related('records__student')

    def perform_create(self, serializer):
        serializer.save()


class AttendanceSessionDetailAPIView(RetrieveAPIView):
    serializer_class = AttendanceSessionSafeSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AttendanceSession.objects.none()
        user = self.request.user

        if user.role == 'admin' and hasattr(user, "dormitory") and user.dormitory:
            return AttendanceSession.objects.filter(
                floor__dormitory__admin=user
            )

        elif user.role == 'floor_leader':
            if hasattr(user, "floor_leader") and user.floor_leader.floor:
                return AttendanceSession.objects.filter(
                    floor=user.floor_leader.floor
                )
            return AttendanceSession.objects.none()

        return AttendanceSession.objects.none()


class AttendanceRecordBulkUpdateAPIView(APIView):
    permission_classes = [IsFloorLeader]

    @swagger_auto_schema(
        request_body=AttendanceRecordBulkUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Bulk update muvaffaqiyatli yakunlandi",
                examples={
                    "application/json": {
                        "updated": [
                            {"id": 10, "student_id": 5, "status": "present"},
                            {"id": 11, "student_id": 6, "status": "absent"}
                        ]
                    }
                }
            ),
            400: "Validation error",
            404: "Session yoki Record topilmadi"
        }
    )
    def patch(self, request, session_id, *args, **kwargs):
        serializer = AttendanceRecordBulkUpdateSerializer(data=request.data)
        if serializer.is_valid():
            records = serializer.validated_data['records']
            updated_records = []

            try:
                session = AttendanceSession.objects.get(id=session_id)
            except AttendanceSession.DoesNotExist:
                return Response(
                    {"detail": f"Session {session_id} topilmadi"},
                    status=status.HTTP_404_NOT_FOUND
                )

            for record in records:
                try:
                    attendance = AttendanceRecord.objects.get(
                        id=record['id'], session=session
                    )
                    if str(attendance.student.id) != str(record['student_id']):
                        return Response(
                            {"detail": f"Record {record['id']} student_id mos emas"},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    attendance.status = record['status']
                    attendance.save()
                    updated_records.append({
                        "id": attendance.id,
                        "student_id": attendance.student.id,
                        "status": attendance.status,
                    })
                except AttendanceRecord.DoesNotExist:
                    return Response(
                        {"detail": f"AttendanceRecord {record['id']} bu Sessionda mavjud emas!"},
                        status=status.HTTP_404_NOT_FOUND
                    )

            return Response({"updated": updated_records}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FloorLeaderListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsDormitoryAdmin]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FloorLeaderCreateSerializer
        return FloorLeaderSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return FloorLeader.objects.none()
        try:
            dormitory = Dormitory.objects.get(admin=self.request.user)
        except Dormitory.DoesNotExist:
            return FloorLeader.objects.none()
        return FloorLeader.objects.filter(floor__dormitory=dormitory).select_related('user', 'floor')


class FloorLeaderDetailAPIView(RetrieveDestroyAPIView):
    serializer_class = FloorLeaderSerializer
    permission_classes = [IsDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return FloorLeader.objects.none()
        try:
            dormitory = Dormitory.objects.get(admin=self.request.user)
        except Dormitory.DoesNotExist:
            return FloorLeader.objects.none()
        return FloorLeader.objects.filter(floor__dormitory=dormitory)

    def perform_destroy(self, instance):
        user = instance.user
        super().perform_destroy(instance)
        if not FloorLeader.objects.filter(user=user).exists() and getattr(user, 'role', None) == 'floor_leader':
            user.role = 'student'
            user.save(update_fields=['role'])


class CollectionListAPIView(ListAPIView):
    serializer_class = CollectionSafeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Collection.objects.none()

        user = self.request.user
        if user.role == 'admin':
            try:
                dormitory = Dormitory.objects.get(admin=user)
            except Dormitory.DoesNotExist:
                return Collection.objects.none()
            return Collection.objects.filter(floor__dormitory=dormitory).order_by('-created_at')

        try:
            leader = FloorLeader.objects.get(user=user)
        except FloorLeader.DoesNotExist:
            return Collection.objects.none()
        return Collection.objects.filter(leader=leader).order_by('-created_at')


class CollectionCreateAPIView(CreateAPIView):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    permission_classes = [IsFloorLeader]


class CollectionDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CollectionSafeSerializer
        return CollectionSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Collection.objects.none()

        user = self.request.user
        if self.request.method == 'GET' and user.role == 'admin':
            try:
                dormitory = Dormitory.objects.get(admin=user)
            except Dormitory.DoesNotExist:
                return Collection.objects.none()
            return Collection.objects.filter(floor__dormitory=dormitory)

        try:
            leader = FloorLeader.objects.get(user=user)
        except FloorLeader.DoesNotExist:
            return Collection.objects.none()
        return Collection.objects.filter(leader=leader)


class CollectionRecordBulkUpdateAPIView(APIView):
    permission_classes = [IsFloorLeader]

    @swagger_auto_schema(
        request_body=CollectionRecordBulkUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Bulk update muvaffaqiyatli yakunlandi",
                examples={
                    "application/json": {
                        "updated": [
                            {"id": 1, "student_id": 101, "status": "To‘lagan"},
                            {"id": 2, "student_id": 102, "status": "To‘lamagan"}
                        ]
                    }
                }
            ),
            400: "Validation error",
            403: "Faqat sardor o‘zgartira oladi",
            404: "Collection yoki Record topilmadi"
        }
    )
    def patch(self, request, collection_id, *args, **kwargs):
        serializer = CollectionRecordBulkUpdateSerializer(data=request.data)
        if serializer.is_valid():
            records = serializer.validated_data['records']
            updated_records = []

            #  Collection mavjudligini tekshirish
            try:
                collection = Collection.objects.get(id=collection_id)
            except Collection.DoesNotExist:
                return Response(
                    {"detail": f"Collection {collection_id} topilmadi"},
                    status=status.HTTP_404_NOT_FOUND
                )

            #  Foydalanuvchi sardorligini tekshirish
            try:
                leader = FloorLeader.objects.get(user=request.user)
            except FloorLeader.DoesNotExist:
                return Response(
                    {"detail": "Siz qavat sardori emassiz"},
                    status=status.HTTP_403_FORBIDDEN
                )

            if collection.leader != leader:
                return Response(
                    {"detail": "Faqat o‘zingizga tegishli yig‘imni o‘zgartirishingiz mumkin"},
                    status=status.HTTP_403_FORBIDDEN
                )

            #  Recordlarni yangilash
            for record in records:
                try:
                    record_obj = CollectionRecord.objects.get(
                        id=record['id'], collection=collection
                    )
                except CollectionRecord.DoesNotExist:
                    return Response(
                        {"detail": f"CollectionRecord {record['id']} bu Collectionda mavjud emas!"},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # student_id mosligini tekshirish
                if str(record_obj.student.id) != str(record['student_id']):
                    return Response(
                        {"detail": f"Record {record['id']} student_id mos emas"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                record_obj.status = record['status']
                record_obj.save(update_fields=['status'])
                updated_records.append({
                    "id": record_obj.id,
                    "student_id": record_obj.student.id,
                    "status": record_obj.status
                })

            return Response({"updated": updated_records}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
