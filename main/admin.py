from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, University, Dormitory, Floor, Room, Student, Application, Payment, Province, District, \
    DormitoryImage, Amenity, Task, AnswerForApplication
from django.core.exceptions import ValidationError
from django import forms


class UserAdmin(BaseUserAdmin):

    list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
    search_fields = ['username', 'email']
    list_filter = ['role', 'is_active']

    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
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
    list_display = ('name', 'address', 'university', 'admin')
    search_fields = ['name', 'address']
    list_filter = ['university']

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
    list_display = ('name', 'university', 'dormitory', 'phone')
    search_fields = ['name', 'university', 'dormitory']
    list_filter = ['university', 'dormitory', 'status']

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
admin.site.register(AnswerForApplication)

