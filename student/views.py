from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Student, Application, ApplicationDocument
from .serializers import (
    StudentSerializer, ApplicationSerializer, ApplicationDocumentSerializer,
    ApplicationCreateSerializer, ApplicationUpdateSerializer, StudentCreateSerializer
)
from users.models import User
from .permissions import IsSuperAdmin, IsDormitoryAdmin, IsStudent, IsStudentOrDormitoryAdmin, IsApplicationOwner, IsDocumentOwner


@swagger_auto_schema(tags=["Students"])
class StudentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing students.
    """
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return StudentCreateSerializer
        return StudentSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        elif self.action == 'create':
            return [IsSuperAdmin() | IsDormitoryAdmin()]
        return [IsSuperAdmin()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Student.objects.none()
        user = self.request.user
        if user.is_student:
            return Student.objects.filter(user=user)
        elif user.is_dormitory_admin:
            return Student.objects.filter(dormitory__admin=user)
        return Student.objects.all()

    def perform_create(self, serializer):
        # If super admin is creating, they can specify any dormitory
        if self.request.user.is_super_admin:
            serializer.save()
        # If dormitory admin is creating, their dormitory is automatically assigned
        elif self.request.user.is_dormitory_admin:
            serializer.save()

    @swagger_auto_schema(
        operation_description="Get current student profile",
        responses={
            200: openapi.Response(
                description="Student profile retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'student_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                        'phone': openapi.Schema(type=openapi.TYPE_STRING),
                        'address': openapi.Schema(type=openapi.TYPE_STRING),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                    }
                )
            ),
            404: "Student profile not found"
        }
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        try:
            student = Student.objects.get(user=request.user)
            serializer = self.get_serializer(student)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


@swagger_auto_schema(tags=["Applications"])
class ApplicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing applications.
    """
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return ApplicationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ApplicationUpdateSerializer
        return ApplicationSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsApplicationOwner()]
        return [IsStudentOrDormitoryAdmin()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Application.objects.none()
        user = self.request.user
        if user.is_student:
            return Application.objects.filter(student__user=user)
        elif user.is_dormitory_admin:
            return Application.objects.filter(dormitory__admin=user)
        return Application.objects.all()

    def perform_create(self, serializer):
        student = get_object_or_404(Student, user=self.request.user)
        serializer.save(student=student)

    def perform_update(self, serializer):
        if self.request.user.is_dormitory_admin:
            serializer.save(reviewed_by=self.request.user)
        else:
            serializer.save()


@swagger_auto_schema(tags=["Applications"])
class ApplicationDocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing application documents.
    """
    queryset = ApplicationDocument.objects.all()
    serializer_class = ApplicationDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsDocumentOwner()]
        return [IsStudentOrDormitoryAdmin()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ApplicationDocument.objects.none()
        user = self.request.user
        if user.is_student:
            return ApplicationDocument.objects.filter(application__student__user=user)
        elif user.is_dormitory_admin:
            return ApplicationDocument.objects.filter(application__dormitory__admin=user)
        return ApplicationDocument.objects.all()

    def perform_create(self, serializer):
        application_id = self.request.data.get('application')
        application = get_object_or_404(Application, id=application_id)
        if application.student.user != self.request.user:
            raise permissions.PermissionDenied("You can only upload documents for your own applications")
        serializer.save()
