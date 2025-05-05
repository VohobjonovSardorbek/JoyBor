from rest_framework import permissions
from users.models import User

class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.SUPER_ADMIN

class IsDormitoryAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.DORMITORY_ADMIN

class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.STUDENT

class IsPaymentOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == User.STUDENT:
            return obj.student == request.user
        elif request.user.role == User.DORMITORY_ADMIN:
            return obj.dormitory.admin == request.user
        return request.user.role == User.SUPER_ADMIN

class IsSubscriptionOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == User.DORMITORY_ADMIN:
            return obj.dormitory.admin == request.user
        return request.user.role == User.SUPER_ADMIN 