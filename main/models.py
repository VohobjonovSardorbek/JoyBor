from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'student'),
        ('admin', 'admin'),
        ('ijarachi', 'ijarachi'),  # yangi
    )
    role = models.CharField(choices=ROLE_CHOICES, max_length=20)
    email = models.EmailField(blank=True, null=True, unique=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    image = models.ImageField(upload_to='user_profiles/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    # Qo'shimcha maydonlar:
    address = models.CharField(max_length=255, blank=True, null=True)
    telegram = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} profili"


class Province(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class District(models.Model):
    name = models.CharField(max_length=255)
    province = models.ForeignKey(Province, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class University(models.Model):
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    contact = models.TextField(blank=True, null=True)
    logo = models.ImageField(blank=True, null=True)

    class Meta:
        verbose_name = 'University'
        verbose_name_plural = 'Universities'

    def __str__(self):
        return self.name


class Amenity(models.Model):
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Dormitory(models.Model):
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255)
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    # yangi
    month_price = models.IntegerField(blank=True, null=True)
    year_price = models.IntegerField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    rating = models.PositiveIntegerField(blank=True, null=True,
                                         validators=[MinValueValidator(1), MaxValueValidator(5)])  # validator
    distance_to_university = models.FloatField(blank=True, null=True, help_text="Universitetgacha masofa (km)")

    amenities = models.ManyToManyField(Amenity, related_name='dormitories')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Dormitory'
        verbose_name_plural = 'Dormitories'

    def __str__(self):
        return self.name


class DormitoryImage(models.Model):
    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='dormitory_images', blank=True, null=True)

    def __str__(self):
        return self.dormitory.name


class Rule(models.Model):
    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE, related_name='rules')
    rule = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Rule'
        verbose_name_plural = 'Rules'

    def __str__(self):
        return self.rule


class Floor(models.Model):
    name = models.CharField(max_length=120)
    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE)
    gender = models.CharField(choices=(('female', 'female'), ('male', 'male')), max_length=20, default='male')

    class Meta:
        verbose_name = 'Floor'
        verbose_name_plural = 'Floors'

    def __str__(self):
        return self.name


class Room(models.Model):
    name = models.CharField(max_length=120)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE)
    capacity = models.IntegerField()
    currentOccupancy = models.IntegerField(default=0)
    gender = models.CharField(choices=(('female', 'female'), ('male', 'male')), max_length=20, default='male')
    status = models.CharField(choices=(('AVAILABLE', 'AVAILABLE'), ('PARTIALLY_OCCUPIED', 'PARTIALLY_OCCUPIED'),
                                       ('FULLY_OCCUPIED', 'FULLY_OCCUPIED')), max_length=20, default='AVAILABLE')

    class Meta:
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'

    def __str__(self):
        return self.name


class Student(models.Model):
    COURSE_CHOICES = (
        ('1-kurs', '1-kurs'),
        ('2-kurs', '2-kurs'),
        ('3-kurs', '3-kurs'),
        ('4-kurs', '4-kurs'),
        ('5-kurs', '5-kurs'),
    )
    Gender_CHOICES = (
        ('Erkak', 'Erkak'),
        ('Ayol', 'Ayol'),
    )
    STATUS_CHOICES = (
        ('Qarzdor', 'Qarzdor'),
        ('Haqdor', 'Haqdor'),
        ('Tekshirilmaydi', 'Tekshirilmaydi'),
    )
    name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120, blank=True, null=True)  # yangi
    middle_name = models.CharField(max_length=120, blank=True, null=True)  # yangi
    province = models.ForeignKey(Province, on_delete=models.CASCADE, default=1)  # yangi
    district = models.ForeignKey(District, on_delete=models.CASCADE, default=1)  # yangi
    faculty = models.CharField(max_length=120, blank=True, null=True)
    direction = models.CharField(max_length=120, blank=True, null=True)  # yangi
    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE,blank=True, null=True, related_name='students')  # yangi
    passport = models.CharField(max_length=9, unique=True, blank=True, null=True)
    group = models.CharField(max_length=120, blank=True, null=True)
    course = models.CharField(max_length=120, choices=COURSE_CHOICES, default='1-kurs')  # yangi
    gender = models.CharField(max_length=120, choices=Gender_CHOICES, default='Erkak')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='students', blank=True, null=True)
    phone = models.CharField(blank=True, null=True, max_length=25)
    picture = models.ImageField(upload_to='student_pictures/', blank=True, null=True)  # yangi
    passport_image_first = models.ImageField(upload_to='passport_image/', blank=True, null=True)
    passport_image_second = models.ImageField(upload_to='passport_image/', blank=True, null=True)
    privilege = models.BooleanField(default=False)
    privilege_share = models.PositiveIntegerField(default=0)
    accepted_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=120, choices=STATUS_CHOICES, default='Tekshirilmaydi')
    PLACEMENT_STATUS_CHOICES = (
        ('Qabul qilindi', 'Qabul qilindi'),
        ('Joylashdi', 'Joylashdi'),
    )

    placement_status = models.CharField(
        max_length=50,
        choices=PLACEMENT_STATUS_CHOICES,
        default='Qabul qilindi'
    )

    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    def __str__(self):
        return self.name


class Application(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'PENDING'),
        ('APPROVED', 'APPROVED'),
        ('REJECTED', 'REJECTED'),
        ('CANCELLED', 'CANCELLED')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE)
    status = models.CharField(choices=STATUS_CHOICES, max_length=20, default='PENDING')
    comment = models.TextField(blank=True, null=True)
    admin_comment = models.TextField(blank=True, null=True)
    document = models.FileField(blank=True, null=True)
    name = models.CharField(max_length=255)
    fio = models.CharField(blank=True, null=True, max_length=255)
    city = models.CharField(blank=True, null=True, max_length=255)
    village = models.CharField(blank=True, null=True, max_length=255)
    university = models.CharField(blank=True, null=True, max_length=255)
    phone = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    direction = models.CharField(blank=True, null=True, max_length=255)
    user_image = models.ImageField(upload_to='student_pictures/', blank=True, null=True)
    passport_image_first = models.ImageField(upload_to='passport_image/', blank=True, null=True)
    passport_image_second = models.ImageField(upload_to='passport_image/', blank=True, null=True)

    class Meta:
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'

    def __str__(self):
        return self.name


# class AnswerForApplication(models.Model):
#     application = models.ForeignKey(Application, on_delete=models.CASCADE)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     comment = models.TextField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return self.application.name


class Payment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE)
    amount = models.IntegerField()
    paid_date = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateField(blank=True, null=True)  # yangi
    method = models.CharField(choices=(('Cash', 'Cash'), ('Card', 'Card')), max_length=20)
    status = models.CharField(choices=(('APPROVED', 'APPROVED'), ('CANCELLED', 'CANCELLED')),
                              max_length=20)
    comment = models.TextField(blank=True, null=True)  # yangi

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return self.student.name


class Task(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Kutilmoqda'),
        ('IN_PROGRESS', 'Jarayonda'),
        ('COMPLETED', 'Bajarilgan'),
    )
    status = models.CharField(choices=STATUS_CHOICES, max_length=20, default='PENDING')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description


class Apartment(models.Model):
    # Asosiy ma'lumotlar
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # Joylashuv va narx
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='apartments')
    exact_address = models.CharField(max_length=255, blank=True, null=True)
    monthly_price = models.IntegerField(blank=True, null=True)
    # nearby_university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='apartments')
    # distance_to_university = models.FloatField(blank=True, null=True, help_text="Universitetgacha masofa (km)")

    # Xona ma'lumotlari
    ROOM_TYPE_CHOICES = (
        ('1 kishilik', '1 kishilik'),
        ('2 kishilik', '2 kishilik'),
        ('3 kishilik', '3 kishilik'),
        ('Oilaviy', 'Oilaviy'),
    )
    GENDER_CHOICES = (
        ('Aralash', 'Aralash'),
        ('Erkak', 'Erkak'),
        ('Ayol', 'Ayol'),
    )
    room_type = models.CharField(max_length=32, choices=ROOM_TYPE_CHOICES, default='Oilaviy')
    gender = models.CharField(max_length=16, choices=GENDER_CHOICES, default='Erkak')
    total_rooms = models.PositiveIntegerField(default=1)
    available_rooms = models.PositiveIntegerField(default=1)
    phone_number = models.CharField(blank=True, null=True, max_length=25)

    # Qulayliklar
    amenities = models.ManyToManyField(Amenity, related_name='apartments')

    # Qoidalar
    # rules_uz = models.JSONField(default=list, blank=True, null=True, help_text="O‘zbekcha qoidalar ro‘yxati")
    # rules_ru = models.JSONField(default=list, blank=True, null=True, help_text="Ruscha qoidalar ro‘yxati")

    # Qo'shimcha
    # is_recommended = models.BooleanField(default=False, help_text="Tavsiya etilgan sifatida belgilash")
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='apartments')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class ApartmentImage(models.Model):
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='apartment_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.apartment.title} - {self.id}"


# class Notification(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
#     message = models.CharField(max_length=255)
#     is_read = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"{self.user} - {self.message}"


class Notification(models.Model):
    TARGET_CHOICES = (
        ('all_students', 'Barcha studentlar'),
        ('all_admins', 'Barcha adminlar'),
        ('specific_user', 'Ma\'lum foydalanuvchi'),
    )
    
    message = models.TextField(help_text="Bildirishnoma matni")
    image = models.ImageField(upload_to='notifications/', blank=True, null=True, help_text="Bildirishnoma rasmi")
    
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES, default='all_students')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, 
                                   help_text="Agar specific_user tanlansa, bu foydalanuvchi")
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, help_text="Bildirishnoma faolmi")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bildirishnoma'
        verbose_name_plural = 'Bildirishnomalar'
    
    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class UserNotification(models.Model):
    """Foydalanuvchiga yuborilgan bildirishnomalar"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_notifications')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='recipients')
    is_read = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-received_at']
        unique_together = ['user', 'notification']
    
    def __str__(self):
        return f"{self.user.username} - {self.notification.title}"