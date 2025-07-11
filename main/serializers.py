from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from .models import *
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.contrib.auth.password_validation import validate_password


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


class UserProfileSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['image', 'bio', 'phone', 'birth_date', 'address', 'telegram']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            if request is not None:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class StudentRegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'username', 'password', 'password2', 'email']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Parollar mos emas!")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User(
            username=validated_data['username'],
            first_name=validated_data.get('first_name', ''),
            role='student'
        )
        user.set_password(validated_data['password'])
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


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = '__all__'


class DormitorySafeSerializer(serializers.ModelSerializer):
    university = UniversitySerializer(read_only=True)
    admin = UserSerializer(read_only=True)
    images = DormitoryImageSafeSerializer(read_only=True, many=True)
    total_capacity = serializers.SerializerMethodField()
    available_capacity = serializers.SerializerMethodField()
    total_rooms = serializers.SerializerMethodField()
    amenities = AmenitySerializer(read_only=True, many=True)

    class Meta:
        model = Dormitory
        fields = ['id', 'university', 'admin', 'name', 'address',
                  'description', 'images', 'month_price', 'year_price',
                  'latitude', 'longitude', 'amenities',
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
                  'latitude', 'longitude']

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


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status']

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
                  'payments', 'total_payment', 'accepted_date', 'group', 'passport', 'course', 'gender']
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
                  'direction', 'floor', 'room', 'phone', 'picture', 'privilege', 'accepted_date', 'passport', 'group', 'course', 'gender']
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
    user = UserSerializer(read_only=True)

    class Meta:
        model = Application
        fields = '__all__'


class ApplicationSerializer(serializers.ModelSerializer):
    dormitory = serializers.PrimaryKeyRelatedField(queryset=Dormitory.objects.all(), write_only=True)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), write_only=True)

    class Meta:
        model = Application
        fields = '__all__'

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
                application__dormitory__admin=user
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

