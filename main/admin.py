from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *
from django.core.exceptions import ValidationError
from django import forms


class UserAdmin(BaseUserAdmin):

    list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
    search_fields = ['username', 'email']
    list_filter = ['role', 'is_active']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Custom', {'fields': ('role',)}),  # Bu qo‘shildi
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'role', 'email', 'password1', 'password2'),
        }),
    )

admin.site.register(User, UserAdmin)


class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')
    search_fields = ['name']

admin.site.register(University, UniversityAdmin)


class DormitoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'university', 'admin', 'is_active')
    search_fields = ['name', 'address']
    list_filter = ['university', 'is_active']

admin.site.register(Dormitory, DormitoryAdmin)


class FloorAdmin(admin.ModelAdmin):
    list_display = ('name', 'dormitory')
    search_fields = ['room']
    list_filter = ['dormitory']

admin.site.register(Floor, FloorAdmin)


class RoomAdmin(admin.ModelAdmin):
    list_display = ('floor', 'name')
    search_fields = ['floor', 'name']
    list_filter = ['floor', 'capacity', 'status']

admin.site.register(Room, RoomAdmin)


class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'dormitory')
    search_fields = ['name', 'dormitory']
    list_filter = ['dormitory', 'floor']

admin.site.register(Student, StudentAdmin)


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'dormitory', 'phone')
    search_fields = ['name', 'dormitory']
    list_filter = ['dormitory', 'status']

admin.site.register(Application, ApplicationAdmin)


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'dormitory')
    search_fields = ['student', 'dormitory']
    list_filter = ['dormitory', 'status']

admin.site.register(Payment, PaymentAdmin)
admin.site.register(Province)
admin.site.register(District)
admin.site.register(DormitoryImage)
admin.site.register(Amenity)
admin.site.register(Task)
admin.site.register(Apartment)
admin.site.register(ApartmentImage)
admin.site.register(Notification)
admin.site.register(UserNotification)
admin.site.register(Like)
admin.site.register(ApplicationNotification)
admin.site.register(UserProfile)
admin.site.register(FloorLeader)
admin.site.register(AttendanceSession)
admin.site.register(AttendanceRecord)
admin.site.register(Collection)
admin.site.register(CollectionRecord)

