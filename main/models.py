from datetime import date
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    role = models.CharField(choices=(('student', 'student'), ('admin', 'admin')), max_length=20)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username


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


class Dormitory(models.Model):
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255)
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    #yangi
    month_price = models.IntegerField(blank=True, null=True)
    year_price = models.IntegerField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    #qo'shimcha qulayliklar
    has_wifi = models.BooleanField(default=False)
    has_library = models.BooleanField(default=False)
    has_gym = models.BooleanField(default=False)
    has_classroom = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Dormitory'
        verbose_name_plural = 'Dormitories'

    def __str__(self):
        return self.name


class DormitoryImage(models.Model):
    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='dormitory_images' ,blank=True, null=True)

    def __str__(self):
        return self.dormitory.name


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
    ROOM_TYPE_CHOICES = (
        ("3-Kishilik", "3-Kishilik"),
        ('5-Kishillik', '5-Kishillik'),
    )
    room_type = models.CharField(choices=ROOM_TYPE_CHOICES, max_length=20, default='3-Kishilik') #yangi
    gender = models.CharField(choices=(('female', 'female'), ('male', 'male')), max_length=20, default='male')
    status = models.CharField(choices=(('AVAILABLE', 'AVAILABLE'), ('PARTIALLY_OCCUPIED', 'PARTIALLY_OCCUPIED'),
                                       ('FULLY_OCCUPIED', 'FULLY_OCCUPIED')), max_length=20, default='AVAILABLE')

    class Meta:
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'

    def __str__(self):
        return self.name


class Student(models.Model):
    name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120, blank=True, null=True)  # yangi
    middle_name = models.CharField(max_length=120, blank=True, null=True)  # yangi
    province = models.ForeignKey(Province, on_delete=models.CASCADE, default=1)  # yangi
    district = models.ForeignKey(District, on_delete=models.CASCADE, default=1)  # yangi
    faculty = models.CharField(max_length=120)
    direction = models.CharField(max_length=120, blank=True, null=True)  # yangi
    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, default=1, related_name='students')  # yangi
    passport = models.CharField(max_length=9, unique=True, blank=True, null=True)
    group = models.CharField(max_length=120, blank=True, null=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='students')
    phone = models.CharField(blank=True, null=True)
    picture = models.ImageField(upload_to='student_pictures/', blank=True, null=True) #yangi
    TARIF_CHOICES = (
        ('Nogiron', 'Nogiron'),
        ("Boquvchisini yo'qotgan", "Boquvchisini yo'qotgan"),
        ('Yotoqxonada faol', 'Yotoqxonada faol'),
        ('Boshqa', 'Boshqa'),
        ('Oddiy', 'Oddiy'),
    )
    tarif = models.CharField(max_length=120, choices=TARIF_CHOICES, default='Oddiy') #yangi
    IMTIYOZ_CHOICES = (
        ('0%', '0%'),
        ('10%', '10%'),
        ('20%', '20%'),
        ('30%', '30%'),
        ('40%', '40%'),
        ('50%', '50%'),
        ('60%', '60%'),
        ('70%', '70%'),
        ('80%', '80%'),
        ('90%', '90%'),
        ('100%', '100%'),
    )
    imtiyoz = models.CharField(max_length=120, choices=IMTIYOZ_CHOICES, default='0%')
    accepted_date = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    def __str__(self):
        return self.name


class Application(models.Model):
    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    status = models.CharField(choices=(('PENDING', 'PENDING'), ('APPROVED', 'APPROVED'), ('REJECTED', 'REJECTED'),
                                       ('CANCELLED', 'CANCELLED')), max_length=20)
    comment = models.TextField(blank=True, null=True)
    document = models.FileField(blank=True, null=True)
    name = models.CharField(max_length=255)
    fio = models.CharField(blank=True, null=True, max_length=255)
    city = models.CharField(blank=True, null=True, max_length=255)
    village = models.CharField(blank=True, null=True, max_length=255)
    university = models.CharField(blank=True, null=True, max_length=255)
    phone = models.IntegerField()
    passport = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'

    def __str__(self):
        return self.name


class Payment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE)
    amount = models.IntegerField()
    paid_date = models.DateField(auto_now_add=True)
    valid_until = models.DateField(blank=True, null=True) #yangi
    method = models.CharField(choices=(('Cash', 'Cash'), ('Card', 'Card')), max_length=20)
    status = models.CharField(choices=(('APPROVED', 'APPROVED'), ('CANCELLED', 'CANCELLED')),
                              max_length=20)
    comment = models.TextField(blank=True, null=True) # yangi

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return self.student.name
