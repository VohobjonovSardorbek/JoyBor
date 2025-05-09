from rest_framework import permissions
from .models import User

class IsSuperAdmin(permissions.BasePermission):
    """
    Allows access only to super admins.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_super_admin

class IsDormitoryAdmin(permissions.BasePermission):
    """
    Allows access only to dormitory admins.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_dormitory_admin

class IsStudent(permissions.BasePermission):
    """
    Allows access only to students.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_student

class IsSelfOrSuperAdmin(permissions.BasePermission):
    """
    Allows users to edit their own profile or super admins to edit any profile.
    """
    def has_object_permission(self, request, view, obj):
        # Allow super admins to edit any profile
        if request.user.is_super_admin:
            return True
        # Allow users to edit their own profile
        return obj.user == request.user

class IsProfileOwnerOrSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.role == User.SUPER_ADMIN:
            return True
        return obj.user == request.user

class CanManageRoles(permissions.BasePermission):
    """
    Allows only superusers and super admins to manage user roles.
    """
    def has_permission(self, request, view):
        return request.user and request.user.can_manage_roles()

    def has_object_permission(self, request, view, obj):
        return request.user and request.user.can_manage_roles()

class CanCreateDormitoryAdmin(permissions.BasePermission):
    """
    Allows only superusers and super admins to create dormitory admin accounts.
    """
    def has_permission(self, request, view):
        return request.user and request.user.can_create_dormitory_admin() 