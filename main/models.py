from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    username = models.CharField()
    role = models.CharField(choices=(('student', 'student'), ('admin', 'admin')), max_length=20)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username

class University(models.Model):
    name = models.CharField()
    address = models.CharField()
    description = models.TextField(blank=True, null=True)
    contact = models.TextField(blank=True, null=True)
    logo = models.ImageField(blank=True, null=True)

    class Meta:
        verbose_name = 'University'
        verbose_name_plural = 'Universities'

    def __str__(self):
        return self.name



class Dormitory(models.Model):
    name = models.CharField()
    address = models.CharField()
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    photo = models.ImageField(blank=True, null=True)

    class Meta:
        verbose_name = 'Dormitory'
        verbose_name_plural = 'Dormitories'

    def __str__(self):
        return self.name

class Floor(models.Model):
    name = models.CharField()
    floor = models.IntegerField()
    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    gender = models.CharField(choices=(('female', 'female') , ('male' , 'male')), max_length=20)

    class Meta:
        verbose_name = 'Floor'
        verbose_name_plural = 'Floors'

    def __str__(self):
        return self.name

class Room(models.Model):
    name = models.CharField()
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    capacity = models.IntegerField()
    currentOccupancy = models.IntegerField()
    price = models.IntegerField()
    roomType = models.CharField(choices=(('standart', 'standart'), ('vip', 'vip')), max_length=20)
    status = models.CharField(choices=(('AVAILABLE', 'AVAILABLE'), ('PARTIALLY_OCCUPIED', 'PARTIALLY_OCCUPIED'), ('FULLY_OCCUPIED', 'FULLY_OCCUPIED')), max_length=20)
    photo = models.ImageField(blank=True, null=True)

    class Meta:
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'

class Student(models.Model):
    name = models.CharField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    faculty = models.CharField()
    course = models.IntegerField()
    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    phone = models.IntegerField()
    passport = models.IntegerField()

    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    def __str__(self):
        return self.name


class Application(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    status = models.CharField(choices=(('PENDING', 'PENDING'), ('APPROVED', 'APPROVED'), ('REJECTED', 'REJECTED') , ('CANCELLED' , 'CANCELLED')), max_length=20)
    comment = models.TextField(blank=True, null=True)
    document = models.FileField(blank=True, null=True)


    class Meta:
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'

    def __str__(self):
        return self.student.name

class Payment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    amount = models.IntegerField()
    date = models.DateField(auto_now_add=True)
    paymentType = models.CharField(choices=(('Cash' , 'Cash'), ('Card' , 'Card')) ,max_length=20)
    status = models.CharField(choices=(('PENDING', 'PENDING'), ('APPROVED', 'APPROVED'), ('CANCELLED' , 'CANCELLED')) ,max_length=20)

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return self.student.name
