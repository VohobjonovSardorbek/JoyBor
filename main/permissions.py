from rest_framework.permissions import BasePermission
from .models import *

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and Student.objects.filter(user=request.user).exists()

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser

class IsDormitoryAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            Dormitory.objects.filter(admin=request.user).exists()
        )

class IsOwnerOrIsAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (request.user.is_superuser or obj.admin == request.user)


class IsAdminOrDormitoryAdmin(BasePermission):
    def has_permission(self, request, view):
        return IsAdmin().has_permission(request, view) or IsDormitoryAdmin().has_permission(request, view)
