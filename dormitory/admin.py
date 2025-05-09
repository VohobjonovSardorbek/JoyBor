from django.contrib import admin
from .models import (
    University, Picture, Dormitory, Floor, RoomType,
    RoomFacility, Room, RoomBooking
)

class PictureInline(admin.StackedInline):
    model = Picture
    extra = 1

class FloorInline(admin.StackedInline):
    model = Floor
    extra = 1

class RoomInline(admin.StackedInline):
    model = Room
    extra = 1

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'website', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'address')
    ordering = ('name',)

@admin.register(Dormitory)
class DormitoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'university', 'admin', 'status', 'subscription_end_date')
    list_filter = ('status', 'university', 'subscription_end_date')
    search_fields = ('name', 'address', 'university__name')
    inlines = [PictureInline, FloorInline]
    ordering = ('name',)

@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ('dormitory', 'floor_number', 'rooms_number', 'gender_type')
    list_filter = ('dormitory', 'gender_type')
    search_fields = ('dormitory__name',)
    ordering = ('dormitory', 'floor_number')

@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'price_per_month', 'is_active')
    list_filter = ('is_active', 'capacity')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(RoomFacility)
class RoomFacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'dormitory', 'floor', 'room_type', 'status', 'current_occupancy')
    list_filter = ('dormitory', 'floor', 'room_type', 'status')
    search_fields = ('room_number', 'dormitory__name')
    ordering = ('dormitory', 'floor', 'room_number')

@admin.register(RoomBooking)
class RoomBookingAdmin(admin.ModelAdmin):
    list_display = ('room', 'student', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('room__room_number', 'student__username')
    ordering = ('-created_at',)
