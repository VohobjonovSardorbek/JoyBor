from rest_framework import serializers
from .models import Student, Application, ApplicationDocument
from users.serializers import UserSerializer
from dormitory.serializers import DormitorySerializer, RoomSerializer
from dormitory.models import Dormitory

class StudentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            'user', 'student_id', 'middle_name', 'address', 'extra_phone_number',
            'university', 'faculty', 'course', 'social_status', 'discount_percentage',
            'emergency_contact', 'passport_number', 'passport_issue_date',
            'passport_expiry_date'
        ]
        extra_kwargs = {
            'user': {'required': True},
            'student_id': {'required': True},
            'university': {'required': True},
            'faculty': {'required': True},
            'course': {'required': True},
            'emergency_contact': {'required': True},
            'passport_number': {'required': True},
            'passport_issue_date': {'required': True},
            'passport_expiry_date': {'required': True}
        }

    def validate(self, data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required")

        # If dormitory admin is creating student, automatically assign their dormitory
        if request.user.is_dormitory_admin:
            try:
                dormitory = Dormitory.objects.get(admin=request.user)
                data['dormitory'] = dormitory
            except Dormitory.DoesNotExist:
                raise serializers.ValidationError("Dormitory admin must be associated with a dormitory")

        return data

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