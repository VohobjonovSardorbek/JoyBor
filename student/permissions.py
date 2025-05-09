from rest_framework import permissions
from users.models import User

class IsStudent(permissions.BasePermission):
    """
    Allows access only to students.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_student

class IsDormitoryAdmin(permissions.BasePermission):
    """
    Allows access only to dormitory admins.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_dormitory_admin

class IsSuperAdmin(permissions.BasePermission):
    """
    Allows access only to super admins.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_super_admin

class IsStudentOrDormitoryAdmin(permissions.BasePermission):
    """
    Allows access to both students and dormitory admins.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_student or request.user.is_dormitory_admin
        )

class IsApplicationOwner(permissions.BasePermission):
    """
    Allows access to:
    - Super admins: all applications
    - Dormitory admins: applications for their dormitory
    - Students: their own applications
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_super_admin:
            return True
        if request.user.is_student:
            return obj.student.user == request.user
        if request.user.is_dormitory_admin:
            return obj.dormitory.admin == request.user
        return False

class IsDocumentOwner(permissions.BasePermission):
    """
    Allows access to:
    - Super admins: all documents
    - Dormitory admins: documents for applications in their dormitory
    - Students: documents for their own applications
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_super_admin:
            return True
        if request.user.is_student:
            return obj.application.student.user == request.user
        if request.user.is_dormitory_admin:
            return obj.application.dormitory.admin == request.user
        return False 