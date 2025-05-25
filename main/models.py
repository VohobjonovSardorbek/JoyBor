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
    photo = models.ImageField(blank=True, null=True)

    # is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Dormitory'
        verbose_name_plural = 'Dormitories'

    def __str__(self):
        return self.name


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
    name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120, blank=True, null=True)  # yangi
    middle_name = models.CharField(max_length=120, blank=True, null=True)  # yangi
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, default=1)  # yangi
    district = models.ForeignKey(District, on_delete=models.CASCADE, default=1)  # yangi
    faculty = models.CharField(max_length=120)
    direction = models.CharField(max_length=120, blank=True, null=True)  # yangi
    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, default=1, related_name='students')  # yangi
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='students')
    phone = models.IntegerField()
    picture = models.ImageField(upload_to='student_pictures/', blank=True, null=True) #yangi
    discount = models.CharField(max_length=255, blank=True, null=True) #yangi
    social_status = models.CharField(max_length=255, blank=True, null=True) #yangi
    accepted_date = models.DateField(blank=True, null=True)

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

    class Meta:
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'

    def __str__(self):
        return self.name


class Payment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    amount = models.IntegerField()
    date = models.DateField(auto_now_add=True)
    paymentType = models.CharField(choices=(('Cash', 'Cash'), ('Card', 'Card')), max_length=20)
    status = models.CharField(choices=(('PENDING', 'PENDING'), ('APPROVED', 'APPROVED'), ('CANCELLED', 'CANCELLED')),
                              max_length=20)

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return self.student.name
