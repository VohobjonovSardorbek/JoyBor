from rest_framework import serializers
from .models import Student, Application, ApplicationDocument
from users.serializers import UserSerializer
from dormitory.serializers import DormitorySerializer, RoomSerializer

class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    dormitory = DormitorySerializer(read_only=True)
    room = RoomSerializer(read_only=True)

    class Meta:
        model = Student
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class ApplicationSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    dormitory = DormitorySerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)

    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'reviewed_by')

class ApplicationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationDocument
        fields = '__all__'
        read_only_fields = ('uploaded_at',)

class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['dormitory', 'preferred_room_type']
        extra_kwargs = {
            'dormitory': {'required': True},
            'preferred_room_type': {'required': True}
        }

class ApplicationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['status', 'comment']
        extra_kwargs = {
            'status': {'required': True},
            'comment': {'required': False}
        } 