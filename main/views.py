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

from .permissions import *
from .serializers import *
from .models import *
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Count, Sum, F, Case, When, Value, IntegerField, Q
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser
from .filters import StudentFilter, ApplicationFilter, TaskFilter
from django.utils.dateparse import parse_date
from django.utils.timesince import timesince
from django.utils.timezone import localtime, now, is_naive, make_aware
from django.utils import timezone
from .serializers import UserProfileUpdateSerializer


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
    serializer_class = DormitorySerializer

    # parser_classes = [MultiPartParser, FormParser]
    #
    # @swagger_auto_schema(auto_schema=None)
    # def put(self, request, *args, **kwargs):
    #     return super().post(request, *args, **kwargs)
    #
    # @swagger_auto_schema(auto_schema=None)
    # def patch(self, request, *args, **kwargs):
    #     return super().post(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(Dormitory, admin=self.request.user)


class DormitoryCreateAPIView(CreateAPIView):
    queryset = Dormitory.objects.all()
    serializer_class = DormitorySerializer
    permission_classes = [IsAdmin]
    # parser_classes = [MultiPartParser, FormParser]
    #
    # @swagger_auto_schema(
    #     manual_parameters=[
    #         openapi.Parameter('name', openapi.IN_FORM, type=openapi.TYPE_STRING),
    #         openapi.Parameter('address', openapi.IN_FORM, type=openapi.TYPE_STRING),
    #         openapi.Parameter('description', openapi.IN_FORM, type=openapi.TYPE_STRING),
    #         openapi.Parameter('month_price', openapi.IN_FORM, type=openapi.TYPE_NUMBER),
    #         openapi.Parameter('year_price', openapi.IN_FORM, type=openapi.TYPE_NUMBER),
    #         openapi.Parameter('latitude', openapi.IN_FORM, type=openapi.TYPE_NUMBER),
    #         openapi.Parameter('longitude', openapi.IN_FORM, type=openapi.TYPE_NUMBER),
    #         openapi.Parameter(
    #             'images',
    #             openapi.IN_FORM,
    #             type=openapi.TYPE_FILE,
    #             description='Upload one or more images. Use Postman for multiple files.',
    #             required=False
    #         ),
    #     ]
    # )
    # def post(self, request, *args, **kwargs):
    #     return super().post(request, *args, **kwargs)


class DormitoryDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Dormitory.objects.all()
    permission_classes = [IsOwnerOrIsAdmin]

    # parser_classes = [MultiPartParser, FormParser]
    #
    # @swagger_auto_schema(auto_schema=None)
    # def put(self, request, *args, **kwargs):
    #     return super().post(request, *args, **kwargs)
    #
    # @swagger_auto_schema(auto_schema=None)
    # def patch(self, request, *args, **kwargs):
    #     return super().post(request, *args, **kwargs)

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

        user = self.request.user
        dormitory = Dormitory.objects.filter(admin=user).first()

        if not dormitory.exists():
            return Room.objects.none()

        floors = Floor.objects.filter(dormitory=dormitory)
        rooms = Room.objects.filter(floor__in=floors).exclude(status='FULLY_OCCUPIED')

        floor_id = self.request.query_params.get('floor')
        if floor_id:
            if floor_id.isdigit():
                rooms = rooms.filter(floor_id=int(floor_id))
            else:
                return Room.objects.none()

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


class StudentListAPIView(ListAPIView):
    serializer_class = StudentSafeSerializer
    permission_classes = [IsDormitoryAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = StudentFilter
    search_fields = ['name', 'last_name']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Student.objects.none()

        user = self.request.user

        if Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            return Student.objects.filter(dormitory=dormitory)
        return Student.objects.none()


class ExportStudentExcelAPIView(APIView):
    permission_classes = [IsDormitoryAdmin]

    def get(self, request, *args, **kwargs):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Students"

        ws.append([
            'ID',
            'Name',
            'Last Name',
            'Middle Name',
            'Province',
            'District',
            'Faculty',
            'Direction',
            'Group',
            'Course',
            'Gender',
            'Phone',
            'Passport',
            'Privilege',
            'Status',
            'Accepted Date'
        ])
        dormitory = get_object_or_404(Dormitory, admin=request.user)
        students = Student.objects.select_related('province', 'district').filter(dormitory=dormitory)

        for student in students:
            ws.append([
                student.id,
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
                'Ha' if student.privilege else 'Yo\'q',
                student.status or '',
                student.accepted_date.strftime('%Y-%m-%d') if student.accepted_date else ''
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=students.xlsx'
        wb.save(response)
        return response


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
        serializer.fields['room'].queryset = Room.objects.filter(floor__in=floors).exclude(status='FULLY_OCCUPIED')

        province = self.request.data.get('province')
        if province:
            serializer.fields['district'].queryset = District.objects.filter(province=province)
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

        user = self.request.user

        if Dormitory.objects.filter(admin=user).exists():
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

    def perform_update(self, serializer):
        instance = serializer.save()

        if instance.floor and instance.room:
            if instance.placement_status != 'Joylashdi':
                instance.placement_status = 'Joylashdi'
                instance.save()


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
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

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
        ws.title = "Payments"

        ws.append([
            'ID',
            'Student Name',
            'Student Last Name',
            'Student Course',
            'Student Room',
            'Amount',
            'Paid Date',
            'Valid Until',
            'Method',
            'Status',
            'Comment'
        ])

        payments = Payment.objects.select_related('student', 'student__room').filter(dormitory=dormitory)

        for payment in payments:
            ws.append([
                payment.id,
                payment.student.name,
                payment.student.last_name or '',
                payment.student.course or '',
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
        response['Content-Disposition'] = 'attachment; filename=payments.xlsx'
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
        # 1. Dormitory olish
        dormitory = Dormitory.objects.filter(admin=request.user).first()
        if not dormitory:
            return Response({"detail": "Dormitory not found"}, status=404)

        today = now().date()

        # 2. Talabalar statistikasi
        students_stats = Student.objects.filter(dormitory=dormitory).aggregate(
            total=Count('id'),
            male=Count('id', filter=Q(room__gender='male')),
            female=Count('id', filter=Q(room__gender='female')),
        )

        # 3. Xonalar statistikasi
        room_stats = Room.objects.filter(floor__dormitory=dormitory).aggregate(
            total_available=Sum(F('capacity') - F('currentOccupancy')),
            male_rooms=Sum(
                Case(
                    When(gender='male', then=F('capacity') - F('currentOccupancy')),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ),
            female_rooms=Sum(
                Case(
                    When(gender='female', then=F('capacity') - F('currentOccupancy')),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )
        )

        # 4. To‘lovlar statistikasi
        payments = Payment.objects.filter(dormitory=dormitory, status='APPROVED')
        payment_stats = payments.aggregate(
            total_payment=Sum('amount')
        )

        debtor_students = payments.filter(valid_until__lt=today).values('student').distinct().count()
        non_debtor_students = payments.filter(valid_until__gte=today).values('student').distinct().count()

        # 5. Arizalar statistikasi
        applications = Application.objects.filter(dormitory=dormitory)
        application_stats = applications.aggregate(
            total=Count('id'),
            approved=Count('id', filter=Q(status='APPROVED')),
            rejected=Count('id', filter=Q(status='REJECTED')),
        )
        recent_applications = applications.order_by('-created_at')[:10]

        # 6. Yig‘ish
        data = {
            "students": students_stats,
            "rooms": {
                "total_available": room_stats['total_available'] or 0,
                "male_rooms": room_stats['male_rooms'] or 0,
                "female_rooms": room_stats['female_rooms'] or 0,
            },
            "payments": {
                "debtor_students_count": debtor_students,
                "non_debtor_students_count": non_debtor_students,
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
    serializer_class = TaskSerializer
    permission_classes = [IsDormitoryAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TaskFilter

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Task.objects.none()

        user = self.request.user
        return Task.objects.filter(user=user).order_by('-created_at')


class TaskDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsDormitoryAdmin]

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

        # 1. Oxirgi 15 ta tasdiqlangan to‘lov
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
                "time": timesince(localtime(paid_date), now()) + " oldin",
                "datetime": paid_date,
            })

        # 2. Oxirgi 15 ta ariza
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
                "time": timesince(localtime(created_at), now()) + " oldin",
                "datetime": created_at,
            })

        # 3. Oxirgi 15 ta qarzdor talaba
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
                "time": timesince(localtime(accepted_date), now()) + " oldin",
                "datetime": accepted_date,
            })

        # 4. Oxirgi 15 ta yangi talaba
        students = Student.objects.filter(dormitory=dormitory).order_by('-accepted_date')[:15]
        for student in students:
            accepted_date = student.accepted_date
            if is_naive(accepted_date):
                accepted_date = make_aware(accepted_date)
            activities.append({
                "type": "new_student",
                "title": "Yangi talaba qo‘shildi",
                "desc": f"{student.name} - {student.course}",
                "time": timesince(localtime(accepted_date), now()) + " oldin",
                "datetime": accepted_date,
            })

        # Barchasini vaqt bo‘yicha tartiblaymiz va 15 tasini olamiz
        activities = sorted(activities, key=lambda x: x['datetime'], reverse=True)[:15]

        # datetime ni chiqarib tashlaymiz
        for act in activities:
            act.pop('datetime', None)

        return Response({"activities": activities})


class ApartmentListAPIView(ListAPIView):
    queryset = Apartment.objects.all()
    serializer_class = ApartmentSafeSerializer
    permission_classes = [AllowAny]


class ApartmentDetailAPIView(RetrieveAPIView):
    queryset = Apartment.objects.all()
    serializer_class = ApartmentSafeSerializer
    permission_classes = [AllowAny]


class ApartmentCreateAPIView(CreateAPIView):
    serializer_class = ApartmentSerializer
    permission_classes = [IsAuthenticated]
    # parser_classes = [MultiPartParser, FormParser]
    #
    # @swagger_auto_schema(auto_schema=None)
    # def post(self, request, *args, **kwargs):
    #     return super().post(request, *args, **kwargs)


class ApartmentUpdateAPIView(UpdateAPIView):
    queryset = Apartment.objects.all()
    serializer_class = ApartmentSerializer
    permission_classes = [IsIjarachiAdmin]

    # parser_classes = [MultiPartParser, FormParser]
    #
    # @swagger_auto_schema(auto_schema=None)
    # def put(self, request, *args, **kwargs):
    #     return super().post(request, *args, **kwargs)
    #
    # @swagger_auto_schema(auto_schema=None)
    # def patch(self, request, *args, **kwargs):
    #     return super().post(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()
        user = self.request.user
        # Faqat o'ziga tegishli apartmentlar
        return Apartment.objects.filter(user=user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


# class AmenityListAPIView(ListAPIView):
#     queryset = Amenity.objects.all()
#     serializer_class = AmenitySerializer
#     permission_classes = [AllowAny]
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ['type']


# class AmenityCreateAPIView(CreateAPIView):
#     queryset = Amenity.objects.all()
#     serializer_class = AmenitySerializer
#     permission_classes = [IsAdminOrDormitoryAdmin]


class AmenityUpdateAPIView(UpdateAPIView):
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    permission_classes = [IsAdminOrDormitoryAdmin]


# class AmenityDeleteAPIView(DestroyAPIView):
#     queryset = Amenity.objects.all()
#     serializer_class = AmenitySerializer
#     permission_classes = [IsAdminOrDormitoryAdmin]


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


class NotificationListView(ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()

        if not self.request.user.is_authenticated:
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


class NotificationMarkReadView(UpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()

        if not self.request.user.is_authenticated:
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)


class NotificationAdminListView(ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return NotificationAdmin.objects.none()

        if not self.request.user.is_authenticated:
            return NotificationAdmin.objects.none()

        user = self.request.user
        if user.role in ['isDormitoryAdmin', 'isSuperAdmin']:
            return Notification.objects.all().order_by('-created_at')
        return Notification.objects.none()


class NotificationAdminCreateView(CreateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != 'isSuperAdmin':
            raise PermissionDenied("Faqat superadminlar bildirishnoma yaratishi mumkin.")
        serializer.save(created_by=user)


class NotificationAdminDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method in ['PUT', 'PATCH', 'DELETE'] and request.user.role != 'isSuperAdmin':
            raise PermissionDenied("Faqat superadminlar tahrirlashi yoki o‘chirish mumkin.")


class MarkNotificationAsReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = NotificationAdmin.objects.get(pk=pk, user=request.user)
            notification.is_read = True
            notification.save()
            return Response({'detail': 'Notification marked as read.'})
        except Notification.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)


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