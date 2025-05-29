from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from .models import *
from django.db.models import Sum


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


class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = '__all__'


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'


class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = '__all__'



class DormitoryShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dormitory
        fields = ['id', 'name']


class DormitoryImageSafeSerializer(serializers.ModelSerializer):
    dormitory = DormitoryShortSerializer(read_only=True)
    class Meta:
        model = DormitoryImage
        fields = ['id', 'dormitory', 'image']


class DormitoryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DormitoryImage
        fields = ['id', 'image']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        try:
            dormitory = Dormitory.objects.get(admin=user)
        except Dormitory.DoesNotExist:
            raise serializers.ValidationError("Sizga hech qanday yotoqxona biriktirilmagan")

        validated_data['dormitory'] = dormitory

        return super().create(validated_data)



class DormitorySafeSerializer(serializers.ModelSerializer):
    university = UniversitySerializer(read_only=True)
    admin = UserSerializer(read_only=True)
    images = DormitoryImageSafeSerializer(read_only=True, many=True)
    total_capacity = serializers.SerializerMethodField()
    available_capacity = serializers.SerializerMethodField()
    total_rooms = serializers.SerializerMethodField()

    class Meta:
        model = Dormitory
        fields = ['id', 'university', 'admin', 'name', 'address', 'description', 'images', 'month_price', 'year_price',
                  'latitude', 'longitude', 'has_wifi', 'has_library', 'has_gym', 'has_classroom',
                  'total_capacity', 'available_capacity', 'total_rooms']

    def get_total_capacity(self, obj):
        return Room.objects.filter(floor__dormitory=obj).aggregate(total=Sum('capacity'))['total'] or 0

    def get_available_capacity(self, obj):
        rooms = Room.objects.filter(floor__dormitory=obj)
        available = 0
        for room in rooms:
            available += room.capacity - room.currentOccupancy
        return available

    def get_total_rooms(self, obj):
        return Room.objects.filter(floor__dormitory=obj).count()


class DormitorySerializer(serializers.ModelSerializer):
    university = serializers.PrimaryKeyRelatedField(queryset=University.objects.all(), write_only=True)
    admin = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)

    class Meta:
        model = Dormitory
        fields = ['id', 'name', 'university', 'address', 'description', 'admin', 'month_price', 'year_price',
                  'latitude', 'longitude', 'has_wifi', 'has_library', 'has_gym', 'has_classroom']

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
        fields = ['id', 'name', 'gender']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        try:
            dormitory = Dormitory.objects.get(admin=user)
        except Dormitory.DoesNotExist:
            raise serializers.ValidationError("Sizga hech qanday yotoqxona biriktirilmagan")

        validated_data['dormitory'] = dormitory

        return super().create(validated_data)


class StudentShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'name', 'last_name']


class RoomSafeSerializer(serializers.ModelSerializer):
    floor = FloorSerializer(read_only=True)
    students = StudentShortSerializer(read_only=True, many=True)

    class Meta:
        model = Room
        fields = ['id', 'name', 'floor', 'capacity', 'currentOccupancy', 'room_type', 'gender', 'status', 'students']


class RoomSerializer(serializers.ModelSerializer):
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), write_only=True)

    class Meta:
        model = Room
        fields = ['id', 'name', 'floor', 'capacity', 'room_type']

    def create(self, validated_data):
        floor = validated_data.get('floor')
        if floor:
            validated_data['gender'] = floor.gender

        return super().create(validated_data)


class PaymentShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'amount', 'method', 'paid_date', 'valid_until', 'comment']


class FloorShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ['id', 'name']


class RoomShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'name']



class StudentSafeSerializer(serializers.ModelSerializer):
    province = ProvinceSerializer(read_only=True)
    district = DistrictSerializer(read_only=True)
    dormitory = DormitoryShortSerializer(read_only=True)
    floor = DormitoryShortSerializer(read_only=True)
    room = RoomShortSerializer(read_only=True)
    payments = PaymentShortSerializer(read_only=True, many=True)
    total_payment = SerializerMethodField()
    picture = SerializerMethodField()

    class Meta:
        model = Student
        fields = ['id', 'name', 'last_name', 'middle_name', 'province', 'district', 'faculty',
                  'direction', 'dormitory', 'floor', 'room', 'phone', 'picture', 'tarif', 'imtiyoz',
                  'payments', 'total_payment', 'accepted_date', 'group', 'passport']
        read_only_fields = ['accepted_date']

    def get_picture(self, obj):
        request = self.context.get('request')
        if obj.picture and hasattr(obj.picture, 'url'):
            if request is not None:
                return request.build_absolute_uri(obj.picture.url)
            return obj.picture.url
        return None

    def get_total_payment(self, obj):
        return sum(p.amount for p in obj.payments.filter(status='APPROVED'))


class StudentSerializer(serializers.ModelSerializer):
    province = serializers.PrimaryKeyRelatedField(queryset=Province.objects.all(), write_only=True)
    district = serializers.PrimaryKeyRelatedField(queryset=District.objects.all(), write_only=True)
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), write_only=True)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), write_only=True)
    picture = serializers.ImageField(required=False)

    class Meta:
        model = Student
        fields = ['id', 'name', 'last_name', 'middle_name', 'province', 'district', 'faculty',
                  'direction', 'floor', 'room', 'phone', 'picture', 'tarif', 'imtiyoz', 'accepted_date', 'passport', 'group']
        read_only_fields = ['accepted_date']

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

        student = super().create(validated_data)

        room = student.room
        room.currentOccupancy = room.students.count()

        if room.currentOccupancy == 0:
            room.status = 'AVAILABLE'
        elif room.currentOccupancy < room.capacity:
            room.status = 'PARTIALLY_OCCUPIED'
        else:
            room.status = 'FULLY_OCCUPIED'

        room.save()

        return student


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
            'paid_date': {
                'read_only': True,
            }
        }


class PaymentSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all(), write_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'student', 'amount', 'paid_date', 'valid_until', 'method', 'status', 'comment']
        read_only_fields = ['paid_date']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        try:
            dormitory = Dormitory.objects.get(admin=user)
        except Dormitory.DoesNotExist:
            raise serializers.ValidationError('Sizga yotoqxona biriktirilmagan')

        validated_data['dormitory'] = dormitory

        return super().create(validated_data)
