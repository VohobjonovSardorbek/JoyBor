from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import *
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'role', 'email']
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


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'image', 'bio', 'phone', 'birth_date', 'address', 'telegram']

    def validate_username(self, value):
        user = self.instance.user
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("Bu username allaqachon mavjud.")
        return value

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user
        password = validated_data.pop('password', None)

        # Yangilash
        if 'username' in user_data:
            user.username = user_data['username']
        if 'first_name' in user_data:
            user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            user.last_name = user_data['last_name']
        if password:
            user.set_password(password)
        user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance



class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class StudentRegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    phone = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Parollar mos emas!")
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Bu email allaqachon mavjud.")
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError("Bu username allaqachon mavjud.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        phone = validated_data.pop('phone')
        user = User(
            username=validated_data['username'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            email=validated_data.get('email', ''),
            role='student'
        )
        user.set_password(validated_data['password'])
        user.save()

        if hasattr(user, 'profile'):
            user.profile.phone = phone
            user.profile.save()
        return user


class TenantRegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    phone = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password', 'password2']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Parollar mos emas!")
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Bu email allaqachon mavjud.")
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError("Bu username allaqachon mavjud.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        phone = validated_data.pop('phone')
        user = User(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            role='ijarachi'
        )
        user.set_password(validated_data['password'])
        user.save()
        if hasattr(user, 'profile'):
            user.profile.phone = phone
            user.profile.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username_or_email = attrs.get('username')
        password = attrs.get('password')

        # Username orqali qidirish
        user = User.objects.filter(username=username_or_email).first()
        # Email orqali qidirish
        if user is None:
            user = User.objects.filter(email=username_or_email).first()
        if user is None or not user.check_password(password):
            raise serializers.ValidationError('Login yoki parol noto‘g‘ri!')

        data = super().validate({'username': user.username, 'password': password})
        data['role'] = user.role
        return data


class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = ['id', 'name']


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ['id', 'name', 'province']


class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = ['id', 'name', 'address', 'description', 'contact', 'logo']


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


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ['id', 'name', 'is_active']


class RuleSafeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = ['id', 'rule']


class DormitorySafeSerializer(serializers.ModelSerializer):
    university = UniversitySerializer(read_only=True)
    admin = UserSerializer(read_only=True)
    images = DormitoryImageSafeSerializer(read_only=True, many=True)
    total_capacity = serializers.SerializerMethodField()
    available_capacity = serializers.SerializerMethodField()
    total_rooms = serializers.SerializerMethodField()
    amenities = AmenitySerializer(many=True, read_only=True)
    rules = RuleSafeSerializer(many=True, read_only=True)

    class Meta:
        model = Dormitory
        fields = ['id', 'university', 'admin', 'name', 'address',
                  'description', 'images', 'month_price', 'year_price',
                  'latitude', 'longitude', 'amenities',
                  'total_capacity', 'available_capacity', 'total_rooms', 'distance_to_university', 'rules']

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
    # images = serializers.ListField(
    #     child=serializers.ImageField(), write_only=True, required=False
    # )
    distance_to_university = serializers.FloatField(read_only=True)

    class Meta:
        model = Dormitory
        fields = [
            'id', 'name', 'university', 'address', 'description', 'admin',
            'month_price', 'year_price', 'latitude', 'longitude', 'distance_to_university'
        ]

    # def create(self, validated_data):
    #     images = validated_data.pop('images', [])
    #     dormitory = Dormitory.objects.create(**validated_data)
    #     for image in images:
    #         DormitoryImage.objects.create(dormitory=dormitory, image=image)
    #     return dormitory

    # def update(self, instance, validated_data):
    #     images = validated_data.pop('images', None)
    #     for attr, value in validated_data.items():
    #         setattr(instance, attr, value)
    #     instance.save()
    #     if images:
    #         for image in images:
    #             DormitoryImage.objects.create(dormitory=instance, image=image)
    #     return instance


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = ['id', 'rule']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        try:
            dormitory = Dormitory.objects.get(admin=user)
        except Dormitory.DoesNotExist:
            raise serializers.ValidationError('Sizga yotoqxona biriktirilmagan')

        validated_data['dormitory'] = dormitory

        return super().create(validated_data)


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


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'description', 'status']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        validated_data['user'] = user

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
        fields = ['id', 'name', 'floor', 'capacity', 'currentOccupancy', 'gender', 'status', 'students']


class RoomSerializer(serializers.ModelSerializer):
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), write_only=True)

    class Meta:
        model = Room
        fields = ['id', 'name', 'floor', 'capacity']

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
                  'direction', 'dormitory', 'floor', 'room', 'phone', 'picture', 'privilege',
                  'payments', 'total_payment', 'accepted_date', 'group', 'passport', 'course', 'gender', 'placement_status']
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
    province = serializers.PrimaryKeyRelatedField(queryset=Province.objects.all(), write_only=True, required=False)
    district = serializers.PrimaryKeyRelatedField(queryset=District.objects.all(), write_only=True, required=False)
    floor = serializers.PrimaryKeyRelatedField(queryset=Floor.objects.all(), write_only=True, required=False)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), write_only=True, required=False)
    picture = serializers.ImageField(required=False)

    class Meta:
        model = Student
        fields = ['id', 'name', 'last_name', 'middle_name', 'province', 'district', 'faculty',
                  'direction', 'floor', 'room', 'phone', 'picture', 'privilege', 'accepted_date', 'passport', 'group',
                  'course', 'gender']
        read_only_fields = ['accepted_date']
        extra_kwargs = {
            'privilege': {'required': False},
        }

    def validate(self, attrs):
        room = attrs.get('room')

        if room and room.currentOccupancy >= room.capacity:
            raise serializers.ValidationError("Bu xona to'lgan, unga talaba qo'sha olmaysiz")
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Foydalanuvchi aniqlanmadi.")

        try:
            dormitory = Dormitory.objects.get(admin=user)
        except Dormitory.DoesNotExist:
            raise serializers.ValidationError('Sizga yotoqxona biriktirilmagan')

        validated_data['dormitory'] = dormitory

        floor = validated_data.get('floor')
        room = validated_data.get('room')

        if floor and room:
            validated_data['placement_status'] = 'Joylashdi'
        else:
            validated_data['placement_status'] = 'Qabul qilindi'

        student = super().create(validated_data)

        if student.room:
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
    user = UserSerializer(read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'user', 'dormitory', 'status', 'comment', 'document',
            'name', 'fio', 'city', 'village', 'university', 'phone',
            'passport_image_first', 'passport_image_second', 'created_at', 'user_image', 'direction'
        ]


class ApplicationSerializer(serializers.ModelSerializer):
    dormitory = serializers.PrimaryKeyRelatedField(queryset=Dormitory.objects.all(), write_only=True)
    passport_image_first = serializers.ImageField(required=False)
    passport_image_second = serializers.ImageField(required=False)
    user_image = serializers.ImageField(required=False)

    class Meta:
        model = Application
        fields = ['id', 'dormitory', 'status', 'comment', 'document',
            'name', 'fio', 'city', 'village', 'university', 'phone',
            'created_at', 'passport_image_first', 'passport_image_second', 'user_image', 'direction'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        validated_data['user'] = user
        return super().create(validated_data)


class PaymentSafeSerializer(serializers.ModelSerializer):
    student = StudentSafeSerializer(read_only=True)
    room = RoomSafeSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'student', 'room', 'dormitory', 'amount', 'paid_date', 'valid_until', 'method', 'status', 'comment'
        ]
        read_only_fields = ['paid_date']


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


class StudentsStatsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    male = serializers.IntegerField()
    female = serializers.IntegerField()


class RoomsStatsSerializer(serializers.Serializer):
    total_available = serializers.IntegerField()
    male_rooms = serializers.IntegerField()
    female_rooms = serializers.IntegerField()


class PaymentsStatsSerializer(serializers.Serializer):
    debtor_students_count = serializers.IntegerField()
    non_debtor_students_count = serializers.IntegerField()
    total_payment = serializers.IntegerField()


class ApplicationsStatsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    approved = serializers.IntegerField()
    rejected = serializers.IntegerField()


class RecentApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['name', 'city', 'status', 'created_at']


class DashboardSerializer(serializers.Serializer):
    students = StudentsStatsSerializer()
    rooms = RoomsStatsSerializer()
    payments = PaymentsStatsSerializer()
    applications = ApplicationsStatsSerializer()
    recent_applications = RecentApplicationSerializer(many=True)


class MonthlyRevenueSerializer(serializers.Serializer):
    month = serializers.CharField()
    revenue = serializers.IntegerField()

    @staticmethod
    def get_monthly_revenue_for_user(user):
        queryset = (
            Payment.objects
            .filter(
                status='APPROVED',
                dormitory__admin=user
            )
            .annotate(month=TruncMonth('paid_date'))
            .values('month')
            .annotate(revenue=Sum('amount'))
            .order_by('month')
        )

        return [
            {"month": item['month'].strftime('%Y-%m'), "revenue": item['revenue']}
            for item in queryset
        ]


class ApartmentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApartmentImage
        fields = ['id', 'image']


class ApartmentSafeSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    images = ApartmentImageSerializer(read_only=True, many=True)
    amenities = AmenitySerializer(many=True, read_only=True)

    class Meta:
        model = Apartment
        fields = [
            'id', 'title', 'description',
            'province', 'exact_address', 'monthly_price',
            'room_type', 'gender', 'total_rooms',
            'available_rooms', 'amenities',
            'created_at', 'user', 'images', 'phone_number', 'is_active',
        ]

class ApartmentSerializer(serializers.ModelSerializer):
    # images = serializers.ListField(
    #     child=serializers.ImageField(), write_only=True, required=False
    # )

    class Meta:
        model = Apartment
        fields = [
            'id', 'title', 'description',
            'province', 'exact_address', 'monthly_price',
            'room_type', 'gender', 'total_rooms',
            'available_rooms', 'amenities', 'phone_number', 'is_active'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        else:
            raise serializers.ValidationError("User authentication required")
        return super().create(validated_data)

    # def update(self, instance, validated_data):
    #     images = validated_data.pop('images', None)
    #     for attr, value in validated_data.items():
    #         setattr(instance, attr, value)
    #     instance.save()
    #     if images:
    #         for image in images:
    #             ApartmentImage.objects.create(apartment=instance, image=image)
    #     return instance


class AnswerForApplicationSafeSerializer(serializers.ModelSerializer):
    application_name = serializers.CharField(source='application.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = AnswerForApplication
        fields = ['id', 'application', 'application_name', 'user', 'user_username', 'comment', 'created_at']
        read_only_fields = ['created_at', 'user', 'application']


class AnswerForApplicationSerializer(serializers.ModelSerializer):
    application = serializers.PrimaryKeyRelatedField(queryset=Application.objects.all(), write_only=True)

    class Meta:
        model = AnswerForApplication
        fields = ['id', 'application', 'comment']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        else:
            raise serializers.ValidationError("User authentication required")

        return super().create(validated_data)