from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class User(AbstractUser):
    SUPER_ADMIN = 'super_admin'
    DORMITORY_ADMIN = 'dormitory_admin'
    STUDENT = 'student'

    ROLE_CHOICES = [
        (SUPER_ADMIN, _('Super admin')),
        (DORMITORY_ADMIN, _('Dormitory admin')),
        (STUDENT, _('Student')),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=STUDENT,
        verbose_name=_('Role')
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')],
        verbose_name=_('Phone number')
    )
    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True,
        verbose_name=_('Profile image')
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', _('Active')),
            ('inactive', _('Inactive')),
            ('blocked', _('Blocked'))
        ],
        default='active',
        verbose_name=_('Status')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-date_joined']


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True, validators=[
        RegexValidator(regex=r'^\+?1?\d{9,15}$')])  # only allows valid phone numbers
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    status = models.CharField(max_length=20,
                              choices=[('active', 'Faol'), ('inactive', 'Faol emas'), ('blocked', 'Bloklangan')],
                              default='active')

    def __str__(self):
        return f"Profile of {self.user.username}"
