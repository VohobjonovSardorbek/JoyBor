from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profiles.
    """
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'phone_number', 'profile_picture', 'status']
        read_only_fields = ['user']

class UserSerializer(serializers.ModelSerializer):
    """
    Base serializer for User model.
    Role field is only visible to superusers and superadmins.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active']
        read_only_fields = ['is_active']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Only show sensitive fields if user is superuser or super_admin
        if request and (request.user.is_superuser or getattr(request.user, 'is_super_admin', False)):
            return data
        
        # Remove sensitive fields for regular users
        sensitive_fields = ['is_superuser', 'is_staff', 'is_super_admin', 'is_dormitory_admin']
        for field in sensitive_fields:
            data.pop(field, None)
        
        return data

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Only creates student accounts.
    """
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'first_name', 'last_name']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            **validated_data,
            role=User.Role.STUDENT  # Force role to be student
        )
        return user

class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing password.
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords don't match")
        return data

class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting password reset.
    """
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset.
    """
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return data

class DormitoryAdminCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating dormitory admin accounts.
    Only accessible by superusers and superadmins.
    """
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'first_name', 'last_name']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            **validated_data,
            role=User.Role.DORMITORY_ADMIN  # Force role to be dormitory admin
        )
        return user 