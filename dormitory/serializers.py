from rest_framework import serializers
from .models import (
    University, Picture, Dormitory, Floor, RoomType,
    RoomFacility, Room, RoomBooking
)

class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class PictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Picture
        fields = '__all__'
        read_only_fields = ('created_at',)

class DormitorySerializer(serializers.ModelSerializer):
    pictures = PictureSerializer(many=True, read_only=True)
    university = UniversitySerializer(read_only=True)
    admin = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Dormitory
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class DormitoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dormitory
        fields = [
            'name', 'address', 'university', 'description',
            'floors_number', 'rooms_number', 'admin',
            'subscription_end_date', 'status', 'contact_info',
            'latitude', 'longitude'
        ]

class FloorSerializer(serializers.ModelSerializer):
    dormitory = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Floor
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class FloorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = [
            'dormitory', 'floor_number', 'rooms_number',
            'description', 'gender_type'
        ]

class RoomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class RoomFacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomFacility
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class RoomSerializer(serializers.ModelSerializer):
    dormitory = DormitorySerializer(read_only=True)
    floor = FloorSerializer(read_only=True)
    room_type = RoomTypeSerializer(read_only=True)
    facilities = RoomFacilitySerializer(many=True, read_only=True)

    class Meta:
        model = Room
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class RoomCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = [
            'dormitory', 'floor', 'room_type', 'room_number',
            'facilities', 'status', 'current_occupancy',
            'monthly_price', 'room_type_category', 'equipment'
        ]

class RoomBookingSerializer(serializers.ModelSerializer):
    room = RoomSerializer(read_only=True)
    student = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = RoomBooking
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class RoomBookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomBooking
        fields = ['room', 'student', 'start_date', 'end_date', 'status']

class RoomBookingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomBooking
        fields = ['status'] 