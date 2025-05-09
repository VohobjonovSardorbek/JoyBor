from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import User, UserProfile
from .serializers import (
    UserSerializer, UserProfileSerializer, UserRegistrationSerializer,
    UserLoginSerializer, PasswordChangeSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, DormitoryAdminCreateSerializer
)
from .permissions import (
    IsSuperAdmin, IsDormitoryAdmin, IsStudent,
    IsSelfOrSuperAdmin, CanManageRoles, CanCreateDormitoryAdmin
)


@swagger_auto_schema(tags=["Accounts"])
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing users.
    """
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        elif self.action == 'create_dormitory_admin':
            return [CanCreateDormitoryAdmin()]
        elif self.action in ['update', 'partial_update']:
            return [IsSelfOrSuperAdmin()]
        elif self.action in ['destroy']:
            return [IsSuperAdmin()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'register':
            return UserRegistrationSerializer
        elif self.action == 'create_dormitory_admin':
            return DormitoryAdminCreateSerializer
        elif self.action == 'login':
            return UserLoginSerializer
        elif self.action == 'reset_password_request':
            return PasswordResetRequestSerializer
        elif self.action == 'change_password':
            return PasswordChangeSerializer
        elif self.action == 'reset_password_confirm':
            return PasswordResetConfirmSerializer
        return UserSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        user = self.request.user
        if user.is_super_admin:
            return User.objects.all()
        elif user.is_dormitory_admin:
            return User.objects.filter(dormitory__admin=user)
        return User.objects.filter(id=user.id)

    def update(self, request, *args, **kwargs):
        # Remove role from request data to prevent role manipulation
        if 'role' in request.data:
            request.data.pop('role')
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        # Remove role from request data to prevent role manipulation
        if 'role' in request.data:
            request.data.pop('role')
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Register a new user (student only)",
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="User registered successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Login user",
        request_body=UserLoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            401: "Invalid credentials",
            400: "Bad Request"
        }
    )
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'user': UserSerializer(user).data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Change user password",
        request_body=PasswordChangeSerializer,
        responses={
            200: openapi.Response(
                description="Password changed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'error': 'Wrong password'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'status': 'password changed'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Request password reset",
        request_body=PasswordResetRequestSerializer,
        responses={
            200: openapi.Response(
                description="Reset email sent",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            404: "User not found",
            400: "Bad Request"
        }
    )
    @action(detail=False, methods=['post'])
    def reset_password_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                token = get_random_string(length=32)
                user.reset_password_token = token
                user.reset_password_token_expires = timezone.now() + timedelta(hours=24)
                user.save()

                reset_link = f"{settings.FRONTEND_URL}/reset-password/{token}"
                send_mail(
                    'Password Reset Request',
                    f'Click the link to reset your password: {reset_link}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                return Response({'status': 'reset email sent'})
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Confirm password reset",
        request_body=PasswordResetConfirmSerializer,
        responses={
            200: openapi.Response(
                description="Password reset successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Invalid or expired token"
        }
    )
    @action(detail=False, methods=['post'])
    def reset_password_confirm(self, request, token):
        try:
            user = User.objects.get(
                reset_password_token=token,
                reset_password_token_expires__gt=timezone.now()
            )
            serializer = PasswordResetConfirmSerializer(data=request.data)
            if serializer.is_valid():
                user.set_password(serializer.validated_data['new_password'])
                user.reset_password_token = None
                user.reset_password_token_expires = None
                user.save()
                return Response({'status': 'password reset successful'})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Create a dormitory admin account (super admin only)",
        request_body=DormitoryAdminCreateSerializer,
        responses={
            201: openapi.Response(
                description="Dormitory admin created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    @action(detail=False, methods=['post'])
    def create_dormitory_admin(self, request):
        serializer = DormitoryAdminCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'user': UserSerializer(user).data,
                'message': 'Dormitory admin created successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    tags=['User Profile Management'],
    operation_description="User profile management endpoints",
    responses={
        200: openapi.Response(
            description="Success",
            schema=UserProfileSerializer
        )
    }
)
class UserProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user profiles.
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsSelfOrSuperAdmin]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserProfile.objects.none()
        user = self.request.user
        if user.is_super_admin:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=user)

@swagger_auto_schema(tags=["Accounts"])
class RegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

@swagger_auto_schema(tags=["Accounts"])
class LoginView(generics.CreateAPIView):
    """
    API endpoint for user login.
    """
    queryset = User.objects.all()
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

@swagger_auto_schema(tags=["Accounts"])
class LogoutView(generics.GenericAPIView):
    """
    API endpoint for user logout.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)
