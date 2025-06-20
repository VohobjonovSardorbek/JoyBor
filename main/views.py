import openpyxl
from django.http import HttpResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404
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
from django.db.models import Q, F
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser
from .filters import StudentFilter


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
        if self.request.user.is_superuser:
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
        elif Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.filter(admin=user)[0]
            return DormitoryImage.objects.filter(dormitory=dormitory)
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
        dormitories = Dormitory.objects.filter(admin=user)

        if not dormitories.exists():
            return Room.objects.none()

        floors = Floor.objects.filter(dormitory__in=dormitories)
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

    # @swagger_auto_schema(
    #     manual_parameters=[
    #         openapi.Parameter(
    #             'floor',
    #             openapi.IN_QUERY,
    #             description="Floor ID bo‘yicha filterlash",
    #             type=openapi.TYPE_INTEGER
    #         ),
    #     ]
    # )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

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
    permission_classes = [IsDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()
        user = self.request.user

        if Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            return Application.objects.filter(dormitory=dormitory)
        return Application.objects.none()


class ApplicationCreateAPIView(CreateAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [AllowAny]
    queryset = Application.objects.all()


class ApplicationDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()
        user = self.request.user

        if Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            return Application.objects.filter(dormitory=dormitory)
        return Application.objects.none()


class PaymentListAPIView(ListAPIView):
    serializer_class = PaymentSafeSerializer
    permission_classes = [IsDormitoryAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()
        user = self.request.user

        if Dormitory.objects.filter(admin=user).exists():
            dormitory = Dormitory.objects.get(admin=user)
            return Payment.objects.filter(dormitory=dormitory)
        return Payment.objects.none()


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
        try:
            dormitory = Dormitory.objects.get(admin=request.user)
        except Dormitory.DoesNotExist:
            return Response({"error": "Dormitory not found for this admin"}, status=404)

        students = Student.objects.filter(dormitory=dormitory)
        total_students = students.count()
        male_students = students.filter(room__gender='male').count()
        female_students = students.filter(room__gender='female').count()

        rooms = Room.objects.filter(floor__dormitory=dormitory)
        total_available = rooms.aggregate(
            free_spaces=Sum(F('capacity') - F('currentOccupancy'))
        )['free_spaces'] or 0

        male_rooms = rooms.filter(gender='male').aggregate(
            free_spaces=Sum(F('capacity') - F('currentOccupancy'))
        )['free_spaces'] or 0

        female_rooms = rooms.filter(gender='female').aggregate(
            free_spaces=Sum(F('capacity') - F('currentOccupancy'))
        )['free_spaces'] or 0

        payments = Payment.objects.filter(dormitory=dormitory)
        today = timezone.now().date()

        debtor_students_count = payments.filter(
            Q(valid_until__lt=today) & Q(status='APPROVED')
        ).values('student').distinct() or 0

        non_debtor_students_count = payments.filter(
            Q(valid_until__gte=today) & Q(status='APPROVED')
        ).values('student').distinct() or 0

        total_payment = payments.filter(status='APPROVED').aggregate(total=Sum('amount'))['total'] or 0

        applications = Application.objects.filter(dormitory=dormitory)
        total_applications = applications.count()
        approved_applications = applications.filter(status='APPROVED').count()
        rejected_applications = applications.filter(status='REJECTED').count()

        recent_applications = applications.order_by('-created_at')

        data = {
            "students": {
                "total": total_students,
                "male": male_students,
                "female": female_students,
            },
            "rooms": {
                "total_available": total_available,
                "male_rooms": male_rooms,
                "female_rooms": female_rooms,
            },
            "payments": {
                "debtor_students_count": debtor_students_count,
                "non_debtor_students_count": non_debtor_students_count,
                "total_payment": total_payment,
            },
            "applications": {
                "total": total_applications,
                "approved": approved_applications,
                "rejected": rejected_applications,
            },
            "recent_applications": recent_applications
        }

        serializer = DashboardSerializer(data)
        return Response(serializer.data)
