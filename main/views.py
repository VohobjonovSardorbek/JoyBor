import openpyxl
from django.http import HttpResponse
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import *
from rest_framework.permissions import IsAuthenticated, AllowAny
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
from django.utils.timezone import localtime
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


class TenantRegisterAPIView(CreateAPIView):
    serializer_class = TenantRegisterSerializer
    permission_classes = [AllowAny]


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
            'Group',
            'Course',
            'Phone',
            'Passport',
            'Imtiyoz',
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
                student.faculty,
                student.group or '',
                student.course or '',
                student.phone or '',
                student.passport or '',
                student.imtiyoz,
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


class ApplicationDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

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
            'Amount',
            'Paid Date',
            'Valid Until',
            'Method',
            'Status',
            'Comment'
        ])

        payments = Payment.objects.select_related('student').filter(dormitory=dormitory)

        for payment in payments:
            ws.append([
                payment.id,
                payment.student.name,
                payment.student.last_name or '',
                payment.amount,
                payment.paid_date.strftime('%Y-%m-%d') if payment.paid_date else '',
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

        # 1. Oxirgi tasdiqlangan to‘lov
        last_payment = Payment.objects.filter(
            dormitory=dormitory, status='APPROVED'
        ).order_by('-paid_date').first()
        payment_activity = None
        if last_payment:
            payment_activity = {
                "type": "payment_approved",
                "title": "To‘lov tasdiqlandi",
                "desc": f"{last_payment.student.name} - {last_payment.amount:,} so'm",
                "time": timesince(localtime(last_payment.paid_date), timezone.now()) + " oldin"
            }

        # 2. Oxirgi ariza
        last_application = Application.objects.filter(
            dormitory=dormitory
        ).order_by('-created_at').first()
        application_activity = None
        if last_application:
            application_activity = {
                "type": "new_application",
                "title": "Yangi ariza",
                "desc": f"{last_application.name} - {last_application.comment or ''}",
                "time": timesince(localtime(last_application.created_at), timezone.now()) + " oldin"
            }

        # 3. To‘lov kechikishi (qarzdor talabalar)
        debtors = Student.objects.filter(
            dormitory=dormitory,
            status='Qarzdor'
        )
        debt_activity = None
        if debtors.exists():
            last_debt = debtors.order_by('-accepted_date').first()
            debt_activity = {
                "type": "debt",
                "title": "To‘lov kechikishi",
                "desc": f"{debtors.count()} ta talaba qarzdor",
                "time": timesince(localtime(last_debt.accepted_date), timezone.now()) + " oldin"
            }

        # Natijani yig‘amiz
        activities = []
        if payment_activity:
            activities.append(payment_activity)
        if application_activity:
            activities.append(application_activity)
        if debt_activity:
            activities.append(debt_activity)

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

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ApartmentUpdateAPIView(UpdateAPIView):
    queryset = Apartment.objects.all()
    serializer_class = ApartmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

