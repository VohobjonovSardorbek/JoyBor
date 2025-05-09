from django.core.validators import RegexValidator, MinValueValidator
from django.db import models
from users.models import User
from dormitory.models import Dormitory, Room, University


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=50, unique=True)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=300, blank=True, null=True)
    extra_phone_number = models.CharField(max_length=15, blank=True, null=True, validators=[
        RegexValidator(regex=r'^\+?1?\d{9,15}$')])
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    faculty = models.CharField(max_length=100)
    course = models.PositiveSmallIntegerField()
    dormitory = models.ForeignKey(Dormitory, on_delete=models.SET_NULL, null=True, blank=True)
    floor = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)], default=1)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    social_status = models.CharField(max_length=255, blank=True, null=True)
    discount_percentage = models.CharField(max_length=255, blank=True, null=True)
    check_in_date = models.DateField(null=True, blank=True)
    check_out_date = models.DateField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=255)
    passport_number = models.CharField(max_length=50)
    passport_issue_date = models.DateField()
    passport_expiry_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.student_id}"


class Application(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE)
    preferred_room_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Application by {self.student.user.username} for {self.dormitory.name}"


class ApplicationDocument(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='documents')
    document = models.FileField(upload_to='application_documents/')
    document_type = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Document for {self.application}"
