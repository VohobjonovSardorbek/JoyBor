from rest_framework.permissions import BasePermission
from .models import *
from rest_framework.exceptions import PermissionDenied


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and Student.objects.filter(user=request.user).exists()


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser


class IsDormitoryAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.role == 'admin':
            has_dormitory = Dormitory.objects.filter(admin=request.user).exists()
            if not has_dormitory:
                raise PermissionDenied("Sizda yotoqxona mavjud emas.")
            return True
        return False


class IsOwnerOrIsAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (request.user.is_superuser or obj.admin == request.user)


class IsAdminOrDormitoryAdmin(BasePermission):
    def has_permission(self, request, view):
        return IsAdmin().has_permission(request, view) or IsDormitoryAdmin().has_permission(request, view)


class IsIjarachiAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == 'ijarachi' or request.user.is_superuser)

    def has_object_permission(self, request, view, obj):
        # Only the owner of the apartment can update
        return obj.user == request.user or request.user.is_superuser
