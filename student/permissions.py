from rest_framework import permissions
from users.models import User

class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == User.STUDENT

class IsDormitoryAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == User.DORMITORY_ADMIN

class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == User.SUPER_ADMIN

class IsStudentOrDormitoryAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in [User.STUDENT, User.DORMITORY_ADMIN]

class IsApplicationOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == User.STUDENT:
            return obj.student.user == request.user
        elif request.user.role == User.DORMITORY_ADMIN:
            return obj.dormitory.user == request.user
        return True

class IsDocumentOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == User.STUDENT:
            return obj.application.student.user == request.user
        elif request.user.role == User.DORMITORY_ADMIN:
            return obj.application.dormitory.user == request.user
        return True 