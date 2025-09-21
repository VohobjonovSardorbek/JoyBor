from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import *
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as AuthUser
from django.db import transaction
from .models import Application, ApplicationNotification

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


class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'image', 'bio', 'phone', 'birth_date',
                  'address', 'telegram']

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

        # Password validatsiyasi
        validate_password(attrs['password'])

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

        # UserProfile yaratish
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.phone = phone
        profile.save()

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

        # Password validatsiyasi
        validate_password(attrs['password'])

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

        # UserProfile yaratish
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.phone = phone
        profile.save()

        return user


class GoogleLoginSerializer(serializers.Serializer):
    token = serializers.CharField(
        required=True,
        help_text="Google ID token from frontend",
        max_length=5000,
        trim_whitespace=True
    )

    def validate_token(self, value):
        if not value or len(value) < 100:
            raise serializers.ValidationError("Invalid token format")

        # Token formatini tekshirish (JWT format)
        if not value.count('.') == 2:
            raise serializers.ValidationError("Invalid JWT token format")

        return value


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


class UniversityShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = ['id', 'name', 'logo']


class DormitoryShortSerializer(serializers.ModelSerializer):
    university = serializers.SerializerMethodField()

    class Meta:
        model = Dormitory
        fields = ['id', 'name', 'month_price', 'university']

    def get_university(self, obj):
        return obj.university.name


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


class RuleSafeForDormitorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = ['id', 'rule']


class DormitorySafeSerializer(serializers.ModelSerializer):
    university = UniversityShortSerializer(read_only=True)
    admin = UserShortSerializer(read_only=True)
    admin_phone_number = serializers.SerializerMethodField()
    admin_telegram = serializers.SerializerMethodField()
    images = DormitoryImageSerializer(read_only=True, many=True)
    total_capacity = serializers.SerializerMethodField()
    approved_applications = SerializerMethodField()
    accepted_students = SerializerMethodField()
    available_capacity = serializers.SerializerMethodField()
    total_rooms = serializers.SerializerMethodField()
    amenities = AmenitySerializer(many=True, read_only=True)
    rules = RuleSafeForDormitorySerializer(many=True, read_only=True)

    class Meta:
        model = Dormitory
        fields = ['id', 'university', 'admin', 'name', 'address',
                  'description', 'images', 'month_price', 'year_price',
                  'latitude', 'longitude', 'amenities', 'admin_phone_number',
                  'admin_telegram', 'is_active', 'total_capacity', 'accepted_students',
                  'approved_applications', 'available_capacity', 'total_rooms',
                  'distance_to_university', 'rules'
                  ]

    def get_admin_phone_number(self, obj):
        return getattr(obj.admin.profile, 'phone', None)

    def get_admin_telegram(self, obj):
        return getattr(obj.admin.profile, 'telegram', None)

    def get_total_capacity(self, obj):
        return Room.objects.filter(floor__dormitory=obj).aggregate(total=Sum('capacity'))['total'] or 0

    def get_available_capacity(self, obj):
        rooms = Room.objects.filter(floor__dormitory=obj)
        available = 0
        for room in rooms:
            available += room.capacity - room.currentOccupancy
        return available

    def get_accepted_students(self, obj):
        return Student.objects.filter(dormitory=obj, placement_status='Joylashdi').count()

    def get_approved_applications(self, obj):
        return Application.objects.filter(dormitory=obj, status='APPROVED').count()

    def get_total_rooms(self, obj):
        return Room.objects.filter(floor__dormitory=obj).count()


class DormitorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Dormitory
        fields = [
            'name', 'university', 'address', 'description', 'admin', 'amenities', 'is_active',
            'month_price', 'year_price', 'latitude', 'longitude', 'distance_to_university',
        ]


class MyDormitorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Dormitory
        fields = [
            'name', 'university', 'address', 'description', 'amenities', 'is_active',
            'month_price', 'year_price', 'latitude', 'longitude', 'distance_to_university'
        ]


class RuleSafeSerializer(serializers.ModelSerializer):
    dormitory = serializers.StringRelatedField()

    class Meta:
        model = Rule
        fields = ['id', 'dormitory', 'rule']


class RuleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = ['rule']


class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ['id', 'name', 'gender']

    def validate_name(self, value):
        request = self.context.get('request')
        user = request.user

        try:
            dormitory = Dormitory.objects.get(admin=user)
        except Dormitory.DoesNotExist:
            raise serializers.ValidationError("Sizga hech qanday yotoqxona biriktirilmagan")

        # Nom unique bo'lishini tekshirish
        if Floor.objects.filter(dormitory=dormitory, name=value).exists():
            raise serializers.ValidationError(f"'{value}' nomli qavat sizning yotoqxonangizda allaqachon mavjud!")

        return value

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        try:
            dormitory = Dormitory.objects.get(admin=user)
        except Dormitory.DoesNotExist:
            raise serializers.ValidationError("Sizga hech qanday yotoqxona biriktirilmagan")

        validated_data['dormitory'] = dormitory

        return super().create(validated_data)


class FloorShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ['id', 'name']


class TaskSafeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'description', 'status', 'reminder_date', 'created_at']


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'description', 'status', 'reminder_date']

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

    def validate_name(self, value):
        floor = self.initial_data.get('floor')
        if floor:
            # Nom unique bo'lishini tekshirish
            if Room.objects.filter(floor_id=floor, name=value).exists():
                raise serializers.ValidationError(f"'{value}' nomli xona bu qavatda allaqachon mavjud!")
        return value

    def create(self, validated_data):
        floor = validated_data.get('floor')
        if floor:
            validated_data['gender'] = floor.gender

        return super().create(validated_data)


class RoomShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'name']


class PaymentShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'amount', 'method', 'paid_date', 'valid_until', 'comment']


class StudentSafeSerializer(serializers.ModelSerializer):
    province = ProvinceSerializer(read_only=True)
    district = DistrictSerializer(read_only=True)
    dormitory = DormitoryShortSerializer(read_only=True)
    floor = FloorShortSerializer(read_only=True)
    room = RoomShortSerializer(read_only=True)
    payments = PaymentShortSerializer(read_only=True, many=True)
    total_payment = SerializerMethodField()
    picture = SerializerMethodField()

    class Meta:
        model = Student
        fields = ['id', 'name', 'last_name', 'middle_name', 'province', 'district', 'faculty',
                  'direction', 'dormitory', 'floor', 'room', 'phone', 'picture', 'privilege',
                  'payments', 'total_payment', 'accepted_date', 'group', 'passport', 'course',
                  'gender', 'placement_status', 'passport_image_first', 'passport_image_second', 'status',
                  'privilege_share', 'document']
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
    passport_image_first = serializers.ImageField(required=False)
    passport_image_second = serializers.ImageField(required=False)
    document = serializers.FileField(required=False)
    # Arizadan ma'lumotlarni (shu jumladan rasm maydonlarini) ko'chirish uchun
    application_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Student
        fields = [
            'id', 'name', 'last_name', 'middle_name', 'province', 'district', 'faculty',
            'direction', 'floor', 'room', 'phone', 'picture', 'privilege', 'accepted_date',
            'passport', 'group', 'course', 'gender', 'passport_image_first', 'passport_image_second',
            'privilege_share', 'application_id', 'user', 'document'
        ]
        read_only_fields = ['accepted_date', 'user']
        extra_kwargs = {
            'privilege': {'required': False},
        }

    def validate(self, attrs):
        passport = attrs.get('passport')
        if passport:
            passport = passport.upper()
            import re
            if not re.match(r'^[A-Z]{2}\d{7}$', passport):
                raise serializers.ValidationError({
                    'passport_number': "Pasport raqami noto'g'ri. Masalan: AA1234567 formatida bo'lishi kerak."
                })
            attrs['passport'] = passport

        room = attrs.get('room')
        if room:
            current_count = room.students.count()
            if current_count >= room.capacity:
                raise serializers.ValidationError({
                    'room': "Bu xona to'lgan, unga talaba qo'sha olmaysiz."
                })

        return attrs

    @transaction.atomic
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

        # Agar application_id yuborilgan bo'lsa
        application_id = validated_data.pop('application_id', None)
        application_instance = None
        student_user = None

        if application_id is not None:
            application_instance = Application.objects.filter(id=application_id, dormitory=dormitory).first()
            if not application_instance:
                raise serializers.ValidationError({
                    'application_id': 'Ariza topilmadi yoki sizning yotoqxonangizga tegishli emas.'
                })

            # Ariza egasining userini olish
            if application_instance.user:
                student_user = application_instance.user

            # Rasmlarni validated_data ga emas, keyin .save() orqali yozamiz

        # Agar ariza egasining useri yo'q bo'lsa, yangi user yaratish
        if not student_user:
            User = get_user_model()
            username = validated_data.get('passport') or validated_data.get('phone')
            if not username:
                raise serializers.ValidationError("Passport yoki telefon raqami talab qilinadi")

            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError(f"Bu passport/telefon raqami bilan foydalanuvchi allaqachon mavjud")

            student_user = User.objects.create_user(
                username=username,
                password=validated_data.get('name', 'default_password'),
                role='student',
                email=f"{username}@example.com"  # vaqtinchalik email
            )

        validated_data['user'] = student_user

        floor = validated_data.get('floor')
        room = validated_data.get('room')

        if floor and room:
            validated_data['placement_status'] = 'Joylashdi'
        else:
            validated_data['placement_status'] = 'Qabul qilindi'

        # Talabani yaratamiz
        student = super().create(validated_data)

        # Application rasmlarini studentga ko‘chirish
        if application_instance:
            if not student.picture and application_instance.user_image:
                student.picture.save(
                    application_instance.user_image.name,
                    application_instance.user_image.file,
                    save=True
                )
            if not student.passport_image_first and application_instance.passport_image_first:
                student.passport_image_first.save(
                    application_instance.passport_image_first.name,
                    application_instance.passport_image_first.file,
                    save=True
                )
            if not student.passport_image_second and application_instance.passport_image_second:
                student.passport_image_second.save(
                    application_instance.passport_image_second.name,
                    application_instance.passport_image_second.file,
                    save=True
                )
            if not student.document and application_instance.document:
                student.document.save(
                    application_instance.document.name,
                    application_instance.document.file,
                    save=True
                )

        # Agar arizasiz yaratilgan bo'lsa, notification yuborish
        if not application_instance and student_user:
            ApplicationNotification.objects.create(
                user=user,
                message=f"Sizning yangi {validated_data.get('name')} ismli talabangizning ma'lumotlari: "
                        f"login: {student_user.username}, parol: {validated_data.get('name', 'default_password')}"
            )

        return student


class ApplicationSafeSerializer(serializers.ModelSerializer):
    dormitory = DormitoryShortSerializer(read_only=True)
    user = UserShortSerializer(read_only=True)
    province = ProvinceSerializer(read_only=True)
    district = DistrictSerializer(read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'user', 'dormitory', 'name', 'last_name', 'middle_name', 'province',
                  'district', 'faculty', 'direction', 'course', 'group', 'phone', 'passport',
                  'status', 'comment', 'admin_comment', 'document', 'user_image',
                  'passport_image_first', 'passport_image_second', 'created_at',
                  ]


class ApplicationSerializer(serializers.ModelSerializer):
    dormitory = serializers.PrimaryKeyRelatedField(queryset=Dormitory.objects.all(), write_only=True)
    passport_image_first = serializers.ImageField(required=False)
    passport_image_second = serializers.ImageField(required=False)
    user_image = serializers.ImageField(required=False)
    province = serializers.PrimaryKeyRelatedField(queryset=Province.objects.all(), write_only=True, required=False)
    district = serializers.PrimaryKeyRelatedField(queryset=District.objects.all(), write_only=True, required=False)

    class Meta:
        model = Application
        fields = ['id', 'dormitory', 'name', 'last_name', 'middle_name', 'province',
                  'district', 'faculty', 'direction', 'course', 'group', 'phone',
                  'passport', 'status', 'comment', 'admin_comment', 'document', 'user_image',
                  'passport_image_first', 'passport_image_second',
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
        fields = ['name', 'status', 'created_at']


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


class ApartmentImageSafeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApartmentImage
        fields = ['id', 'image']


class ApartmentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApartmentImage
        fields = ['id', 'apartment', 'image', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class ApartmentSafeSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    user_phone_number = serializers.SerializerMethodField()
    images = ApartmentImageSafeSerializer(read_only=True, many=True)
    amenities = AmenitySerializer(many=True, read_only=True)

    class Meta:
        model = Apartment
        fields = [
            'id', 'title', 'description', 'province', 'exact_address',
            'monthly_price', 'room_type', 'gender', 'total_rooms',
            'available_rooms', 'amenities', 'user_phone_number',
            'created_at', 'user', 'images', 'phone_number', 'is_active',
        ]

    def get_user_phone_number(self, obj):
        return getattr(obj.user.profile, 'phone', None)


class ApartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apartment
        fields = [
            'id', 'title', 'description', 'province',
            'exact_address', 'monthly_price', 'room_type',
            'gender', 'total_rooms', 'available_rooms',
            'amenities', 'phone_number', 'is_active'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        else:
            raise serializers.ValidationError("User authentication required")
        return super().create(validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    target_user_username = serializers.CharField(source='target_user.username', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'message', 'image', 'image_url', 'target_type',
            'target_user', 'target_user_username',
            'created_at', 'is_active'
        ]
        read_only_fields = ['created_at']

    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'message', 'image', 'target_type', 'target_user'
        ]

    def validate(self, attrs):
        target_type = attrs.get('target_type')
        target_user = attrs.get('target_user')

        if target_type == 'specific_user' and not target_user:
            raise serializers.ValidationError(
                "Ma'lum foydalanuvchi tanlangan bo'lsa, foydalanuvchi ham ko'rsatilishi kerak")

        if target_type != 'specific_user' and target_user:
            raise serializers.ValidationError(
                "Faqat ma'lum foydalanuvchi tanlanganda foydalanuvchi ko'rsatilishi mumkin")

        return attrs


class UserNotificationSerializer(serializers.ModelSerializer):
    notification = NotificationSerializer(read_only=True)

    class Meta:
        model = UserNotification
        fields = ['id', 'notification', 'is_read', 'received_at']
        read_only_fields = ['user', 'received_at']


class MarkNotificationReadSerializer(serializers.Serializer):
    notification_id = serializers.IntegerField()


class ApplicationNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationNotification
        fields = "__all__"


class ApplicationNotificationReadSerializer(serializers.Serializer):
    notification_id = serializers.IntegerField(help_text="O'qildi deb belgilash uchun notification ID si")


class LikeSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta:
        model = Like
        fields = ['id', 'content_type', 'object_id', 'created_at', 'data']
        read_only_fields = ['user', 'created_at']

    def get_data(self, obj):
        if obj.content_type == 'dormitory':
            dormitory = Dormitory.objects.filter(id=obj.object_id).first()
            if dormitory:
                return {
                    "type": "dormitory",
                    "id": dormitory.id,
                    "name": dormitory.name,
                    "address": dormitory.address,
                    "description": dormitory.description,
                    "month_price": dormitory.month_price,
                    "year_price": dormitory.year_price,
                    "distance_to_university": dormitory.distance_to_university,
                    "is_active": dormitory.is_active,
                    "university_name": dormitory.university.name if dormitory.university else None,
                    "admin_username": dormitory.admin.username if dormitory.admin else None,
                    "total_students": Student.objects.filter(dormitory=dormitory).count(),
                    "approved_applications": Application.objects.filter(dormitory=dormitory, status='APPROVED').count(),
                }
        elif obj.content_type == 'apartment':
            apartment = Apartment.objects.filter(id=obj.object_id).first()
            if apartment:
                return {
                    "type": "apartment",
                    "id": apartment.id,
                    "title": apartment.title,
                    "description": apartment.description,
                    "exact_address": apartment.exact_address,
                    "monthly_price": apartment.monthly_price,
                    "room_type": apartment.room_type,
                    "gender": apartment.gender,
                    "total_rooms": apartment.total_rooms,
                    "available_rooms": apartment.available_rooms,
                    "phone_number": apartment.phone_number,
                    "is_active": apartment.is_active,
                    "province_name": apartment.province.name if apartment.province else None,
                    "owner_username": apartment.user.username if apartment.user else None,
                    "created_at": apartment.created_at,
                }
        return None


class LikeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['content_type', 'object_id']

    def validate(self, attrs):
        content_type = attrs.get('content_type')
        object_id = attrs.get('object_id')

        if content_type == 'dormitory':
            if not Dormitory.objects.filter(id=object_id).exists():
                raise serializers.ValidationError("Dormitory topilmadi")
        elif content_type == 'apartment':
            if not Apartment.objects.filter(id=object_id).exists():
                raise serializers.ValidationError("Apartment topilmadi")
        else:
            raise serializers.ValidationError("Noto'g'ri content_type")

        return attrs


class FloorLeaderCreateSerializer(serializers.ModelSerializer):
    """Floor leader yaratish uchun - user ma'lumotlari bilan birga"""
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(write_only=True)  # 🔹 Email qo‘shildi
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    phone_number = serializers.CharField(write_only=True, required=False)
    picture = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = FloorLeader
        fields = ["id", "floor", "username", "password", "email", "first_name", "last_name"]

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication required")

        floor = attrs.get('floor')
        if not floor:
            raise serializers.ValidationError("Floor talab qilinadi")

        try:
            dormitory = Dormitory.objects.get(admin=user)
        except Dormitory.DoesNotExist:
            raise serializers.ValidationError("Sizga yotoqxona biriktirilmagan")

        if floor.dormitory_id != dormitory.id:
            raise serializers.ValidationError("Faqat o'zingizning yotoqxonangiz qavati uchun sardor tayinlaysiz")

        # Username unique bo‘lishini tekshirish
        username = attrs.get('username')
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("Bu username allaqachon mavjud")

        # Email unique bo‘lishini tekshirish 🔹
        email = attrs.get('email')
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Bu email allaqachon mavjud")

        return attrs

    def create(self, validated_data):
        # User yaratish
        user_data = {
            'username': validated_data.pop('username'),
            'password': validated_data.pop('password'),
            'email': validated_data.pop('email'),  # 🔹 Email qo‘shildi
            'first_name': validated_data.pop('first_name', ''),
            'last_name': validated_data.pop('last_name', ''),
            'role': 'floor_leader'
        }

        user = User.objects.create_user(**user_data)

        validated_data['user'] = user
        return super().create(validated_data)


class FloorLeaderSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    floor = FloorShortSerializer(read_only=True)

    class Meta:
        model = FloorLeader
        fields = ["id", "floor", "user"]


class FloorLeaderShortSerializer(serializers.ModelSerializer):
    user = serializers.CharField(read_only=True)
    floor = serializers.CharField(read_only=True)

    class Meta:
        model = FloorLeader
        fields = ["id", "floor", "user"]

    def get_user(self, obj):
        return getattr(obj, 'user', None)

    def get_floor(self, obj):
        return getattr(obj, 'floor', None)


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student = StudentShortSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        source="student",
        write_only=True
    )

    class Meta:
        model = AttendanceRecord
        fields = ["id", "session", "student", "student_id", "status", "created_at"]
        read_only_fields = ["id", "created_at", "student"]


class AttendanceRecordShortSerializer(serializers.ModelSerializer):
    student = StudentShortSerializer(read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = ["id", "student", "status"]


class RoomGroupedSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    room_name = serializers.CharField()
    students = AttendanceRecordShortSerializer(many=True)


class AttendanceSessionSafeSerializer(serializers.ModelSerializer):
    floor = FloorShortSerializer(read_only=True)
    leader = FloorLeaderShortSerializer(read_only=True)
    date = serializers.DateField(read_only=True)
    rooms = serializers.SerializerMethodField()
    exist_students = serializers.SerializerMethodField()
    absent_students = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceSession
        fields = ["id", "date", "floor", "leader", "rooms", 'exist_students', 'absent_students']

    def get_exist_students(self, obj):
        records = getattr(obj, "records", None)
        if records is None:
            return 0
        return records.filter(status="in").count()

    def get_absent_students(self, obj):
        records = getattr(obj, "records", None)
        if records is None:
            return 0
        return records.filter(status="out").count()

    def get_rooms(self, obj):
        # sessionga tegishli barcha recordlarni olib kelamiz
        records = obj.records.select_related("student__room").all().order_by("student__room__name")

        grouped = {}
        for record in records:
            room = record.student.room
            if not room:
                continue
            if room.id not in grouped:
                grouped[room.id] = {
                    "room_id": room.id,
                    "room_name": room.name,
                    "students": []
                }
            grouped[room.id]["students"].append(record)

        # endi serializer orqali qaytaramiz
        serializer = RoomGroupedSerializer(
            sorted(grouped.values(), key=lambda x: x["room_name"]),
            many=True
        )
        return serializer.data


class AttendanceSessionSerializer(serializers.ModelSerializer):
    floor = serializers.CharField(source="floor.name", read_only=True)
    leader = serializers.CharField(source="leader.user.username", read_only=True)
    date = serializers.DateField(read_only=True, format="%Y-%m-%d")

    class Meta:
        model = AttendanceSession
        fields = ["id", "date", "floor", "leader", "created_at"]
        read_only_fields = ["id", "date", "floor", "leader", "created_at"]

    def create(self, validated_data):

        request = self.context.get("request")
        user = request.user

        #  Foydalanuvchi FloorLeader ekanini tekshiramiz
        try:
            leader = FloorLeader.objects.select_related("floor").get(user=user)
        except FloorLeader.DoesNotExist:
            raise serializers.ValidationError(" Siz qavat sardori emassiz!")

        today = timezone.now().date()

        #  Bugungi kunda shu qavat uchun sessiya allaqachon bormi?
        if AttendanceSession.objects.filter(date=today, floor=leader.floor).exists():
            raise serializers.ValidationError(" Bugungi kunda ushbu qavat uchun davomat allaqachon yaratilgan!")

        #  Session yaratish
        session = AttendanceSession.objects.create(
            floor=leader.floor,
            leader=leader,
        )

        # Shu qavatdagi barcha studentlar uchun AttendanceRecord yaratish
        students = Student.objects.filter(room__floor=leader.floor).only("id")
        records = [
            AttendanceRecord(session=session, student=student, status=AttendanceRecord.Status.IN)
            for student in students
        ]
        AttendanceRecord.objects.bulk_create(records)

        return session


class AttendanceRecordUpdateItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    student_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=AttendanceRecord.Status.choices)


class AttendanceRecordBulkUpdateSerializer(serializers.Serializer):
    records = serializers.ListField(child=AttendanceRecordUpdateItemSerializer())


class CollectionRecordSerializer(serializers.ModelSerializer):
    student = StudentShortSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        source="student",
        write_only=True
    )

    class Meta:
        model = CollectionRecord
        fields = ["id", "collection", "student", "student_id", "status"]
        read_only_fields = ["id", "student"]


class CollectionRecordShortSerializer(serializers.ModelSerializer):
    student = StudentShortSerializer(read_only=True)

    class Meta:
        model = CollectionRecord
        fields = ["id", "student", "status"]


class RoomGroupedSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    room_name = serializers.CharField()
    students = CollectionRecordShortSerializer(many=True)


class CollectionSafeSerializer(serializers.ModelSerializer):
    floor = FloorShortSerializer(read_only=True)
    leader = FloorLeaderShortSerializer(read_only=True)
    rooms = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = ["id", "title", "amount", "description", "deadline", "floor", "leader", "rooms", "created_at"]
        read_only_fields = ["id", "floor", "leader", "rooms", "created_at"]

    def get_rooms(self, obj):
        # sessionga tegishli barcha recordlarni olib kelamiz
        records = obj.records.select_related("student__room").all().order_by("student__room__name")

        grouped = {}
        for record in records:
            room = record.student.room
            if not room:
                continue
            if room.id not in grouped:
                grouped[room.id] = {
                    "room_id": room.id,
                    "room_name": room.name,
                    "students": []
                }
            grouped[room.id]["students"].append(record)

        # serializer orqali qaytarish
        serializer = RoomGroupedSerializer(
            sorted(grouped.values(), key=lambda x: x["room_name"]),
            many=True
        )
        return serializer.data


class CollectionSerializer(serializers.ModelSerializer):
    floor = serializers.CharField(source="floor.name", read_only=True)
    leader = serializers.CharField(source="leader.user.username", read_only=True)
    records = CollectionRecordSerializer(many=True, read_only=True)

    class Meta:
        model = Collection
        fields = ["id", "title", "amount", "description", "deadline", "floor", "leader", "records", "created_at"]
        read_only_fields = ["id", "floor", "leader", "records", "created_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user

        # Foydalanuvchi FloorLeader ekanini tekshirish
        try:
            leader = FloorLeader.objects.get(user=user)
        except FloorLeader.DoesNotExist:
            raise serializers.ValidationError("Faqat qavat sardori yig‘im yaratishi mumkin!")

        # Collection yaratish
        collection = Collection.objects.create(
            leader=leader,
            floor=leader.floor,
            **validated_data
        )

        # Shu qavatdagi barcha studentlar uchun CollectionRecord yaratish
        students = Student.objects.filter(room__floor=leader.floor).only("id")
        records = [
            CollectionRecord(collection=collection, student=student, status=CollectionRecord.Status.UNPAID)
            for student in students
        ]
        CollectionRecord.objects.bulk_create(records)

        return collection


class CollectionRecordUpdateItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    student_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=CollectionRecord.Status.choices)


class CollectionRecordBulkUpdateSerializer(serializers.Serializer):
    """Collection recordlarni bulk update qilish uchun"""
    records = serializers.ListField(child=CollectionRecordUpdateItemSerializer())


class StatisticForLeaderSerializer(serializers.Serializer):
    active_students = serializers.IntegerField()
    collection_degree = serializers.CharField()
    today_attendance = serializers.CharField()
    open_tasks = serializers.IntegerField()


class TaskForLeaderSafeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskForLeader
        fields = ["id", "status", 'description', 'user', 'created_at']


class TaskForLeaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskForLeader
        fields = ["id", "status", 'description']

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        validated_data["user"] = user

        return super().create(validated_data)

class RoomMateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["id", "name", "last_name", "room"]   # kerakli fieldlarni yozing

class ForStudentSerializer(serializers.ModelSerializer):
    roommates = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()
    province = ProvinceSerializer(read_only=True)
    district = DistrictSerializer(read_only=True)
    dormitory = DormitoryShortSerializer(read_only=True)
    floor = FloorShortSerializer(read_only=True)
    room = RoomShortSerializer(read_only=True)
    user = UserShortSerializer(read_only=True)

    class Meta:
        model = Student
        fields = "__all__"
        read_only_fields = ["id", "user"]

    def get_roommates(self, obj):
        if not obj.room:
            return []
        roommates = Student.objects.filter(room=obj.room).exclude(id=obj.id)
        return RoomMateSerializer(roommates, many=True).data

    def get_payments(self, obj):
        payments = obj.payments.all()
        return PaymentShortSerializer(payments, many=True).data


class DutyScheduleSafeSerializer(serializers.ModelSerializer):
    room = RoomShortSerializer(read_only=True)
    floor = FloorShortSerializer(read_only=True)

    class Meta:
        model = DutySchedule
        fields = ['id', 'floor', 'room', 'date', 'created_at']


class DutyScheduleSerializer(serializers.ModelSerializer):

    class Meta:
        model = DutySchedule
        fields = ['id', 'room', 'date', 'created_at']
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user

        leader = getattr(user, "floor_leader", None)
        if leader is None:
            raise serializers.ValidationError("Siz floor leader emassiz.")

        validated_data['floor'] = leader.floor
        return super().create(validated_data)

