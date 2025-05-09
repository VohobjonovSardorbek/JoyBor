from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class User(AbstractUser):
    """
    Custom user model with role-based access control.
    """
    class Role(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
        DORMITORY_ADMIN = 'DORMITORY_ADMIN', 'Dormitory Admin'
        STUDENT = 'STUDENT', 'Student'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT
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
    reset_password_token = models.CharField(max_length=100, blank=True, null=True)
    reset_password_token_expires = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']

    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    @property
    def is_dormitory_admin(self):
        return self.role == self.Role.DORMITORY_ADMIN

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    def can_create_dormitory_admin(self):
        """Check if user can create dormitory admin accounts."""
        return self.is_superuser or self.is_super_admin

    def can_manage_roles(self):
        """Check if user can manage user roles."""
        return self.is_superuser or self.is_super_admin

    def can_access_admin_panel(self):
        """Check if user can access the admin panel."""
        return self.is_superuser or self.is_super_admin

    def save(self, *args, **kwargs):
        # Prevent role changes through normal save
        if self.pk:  # If this is an update
            old_instance = User.objects.get(pk=self.pk)
            if old_instance.role != self.role and not (self.is_superuser or self.is_super_admin):
                self.role = old_instance.role
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')],
        verbose_name=_('Phone number')
    )
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        verbose_name=_('Profile picture')
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    @property
    def status(self):
        """Get status from associated user."""
        return self.user.status

    class Meta:
        ordering = ['-created_at']
