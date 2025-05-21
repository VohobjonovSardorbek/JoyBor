from rest_framework import serializers
from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, attrs):
        request_user = self.context['request'].user
        role = attrs.get('role')
        dormitory = attrs.get('dormitory')

        if request_user.role == 'admin':
            if role in ['teacher', 'student', 'manager']:
                if not dormitory or dormitory.admin != request_user:
                    raise serializers.ValidationError("Siz faqat o'z Dormitoryingizga foydalanuvchi qo'sha olasiz.")
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = '__all__'


class DormitorySafeSerializer(serializers.ModelSerializer):
    university = UniversitySerializer(read_only=True)
    admin = UserSerializer(read_only=True)

    class Meta:
        model = Dormitory
        fields = ['id', 'university', 'admin', 'name', 'address', 'description', 'photo']


class DormitorySerializer(serializers.ModelSerializer):
    university = serializers.PrimaryKeyRelatedField(queryset=University.objects.all(), write_only=True)
    admin = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)

    class Meta:
        model = Dormitory
        fields = ['id', 'name', 'university', 'address', 'description', 'admin', 'photo']

    def validate(self, attrs):
        admin = attrs.get('admin')
        queryset = Dormitory.objects.filter(admin=admin)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError('Siz tanlagan adminga allaqachon yotoqxona biriktirilgan')

        return attrs


class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ['id', 'name', 'floor', 'description', 'gender']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        try:
            dormitory = Dormitory.objects.get(admin=user)
        except Dormitory.DoesNotExist:
            raise serializers.ValidationError("Sizga hech qanday yotoqxona biriktirilmagan")

        validated_data['dormitory'] = dormitory

        return super().create(validated_data)


class RoomSafeSerializer(serializers.ModelSerializer):
    floor = FloorSerializer(read_only=True)

    class Meta:
        model = Room
        fields = '__all__'


class RoomSerializer(serializers.ModelSerializer):
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), write_only=True)

    class Meta:
        model = Room
        fields = '__all__'


class StudentSafeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    university = UniversitySerializer(read_only=True)
    dormitory = DormitorySafeSerializer(read_only=True)
    room = RoomSafeSerializer(read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'name', 'user', 'university', 'faculty', 'course', 'dormitory', 'room', 'phone', 'passport']


class StudentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='student'), write_only=True)
    university = serializers.PrimaryKeyRelatedField(queryset=University.objects.all(), write_only=True)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), write_only=True)

    class Meta:
        model = Student
        fields = ['id', 'name', 'user', 'university', 'faculty', 'course', 'room', 'phone', 'passport']

    def validate(self, attrs):
        room = attrs.get('room')

        if room.currentOccupancy >= room.capacity:
            raise serializers.ValidationError("Bu xona to'lgan, unga talaba qo'sha olmaysiz")
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        try:
            dormitory = Dormitory.objects.get(admin=user)
        except Dormitory.DoesNotExist:
            raise serializers.ValidationError('Sizga yotoqxona biriktirilmagan')

        validated_data['dormitory'] = dormitory

        return super().create(validated_data)


class ApplicationSafeSerializer(serializers.ModelSerializer):
    dormitory = DormitorySafeSerializer(read_only=True)
    room = RoomSafeSerializer(read_only=True)

    class Meta:
        model = Application
        fields = '__all__'


class ApplicationSerializer(serializers.ModelSerializer):
    dormitory = serializers.PrimaryKeyRelatedField(queryset=Dormitory.objects.all(), write_only=True)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), write_only=True)

    class Meta:
        model = Application
        fields = '__all__'


class PaymentSafeSerializer(serializers.ModelSerializer):
    student = StudentSafeSerializer(read_only=True)
    room = RoomSafeSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'

        extra_kwargs = {
            'date': {
                'read_only': True,
            }
        }


class PaymentSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all(), write_only=True)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), write_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'student', 'room', 'amount', 'date', 'paymentType', 'status']
        read_only_fields = ['date']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        try:
            dormitory = Dormitory.objects.get(admin=user)
        except Dormitory.DoesNotExist:
            raise serializers.ValidationError('Sizga yotoqxona biriktirilmagan')

        validated_data['dormitory'] = dormitory

        return super().create(validated_data)
