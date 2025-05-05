from users.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class University(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    address = models.CharField(max_length=300, verbose_name=_('Address'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    contact_info = models.TextField(blank=True, null=True, verbose_name=_('Contact information'))
    website = models.URLField(blank=True, null=True, verbose_name=_('Website'))
    logo = models.ImageField(upload_to='university_logos/', blank=True, null=True, verbose_name=_('Logo'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('University')
        verbose_name_plural = _('Universities')
        ordering = ['name']


class Picture(models.Model):
    image = models.ImageField(upload_to='dormitory_images/', verbose_name=_('Image'))
    dormitory = models.ForeignKey('Dormitory', on_delete=models.CASCADE, related_name='pictures')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.dormitory.name}"

    class Meta:
        verbose_name = _('Picture')
        verbose_name_plural = _('Pictures')
        ordering = ['-created_at']


class Dormitory(models.Model):
    STATUS_CHOICES = (
        ('active', _('Active')),
        ('pending', _('Pending')),
        ('inactive', _('Inactive'))
    )

    name = models.CharField(max_length=255, verbose_name=_('Name'))
    address = models.CharField(max_length=300, verbose_name=_('Address'))
    university = models.ForeignKey(University, on_delete=models.CASCADE, verbose_name=_('University'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    floors_number = models.PositiveSmallIntegerField(verbose_name=_('Number of floors'))
    rooms_number = models.PositiveSmallIntegerField(verbose_name=_('Number of rooms'))
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_dormitories',
                              verbose_name=_('Admin'))
    subscription_end_date = models.DateField(verbose_name=_('Subscription end date'))
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='active', verbose_name=_('Status'))
    contact_info = models.TextField(blank=True, null=True, verbose_name=_('Contact information'))
    latitude = models.FloatField(blank=True, null=True, verbose_name=_('Latitude'))
    longitude = models.FloatField(blank=True, null=True, verbose_name=_('Longitude'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Dormitory')
        verbose_name_plural = _('Dormitories')
        ordering = ['name']


class Floor(models.Model):
    GENDER_CHOICES = (
        ('male', _('Male')),
        ('female', _('Female')),
    )

    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE, related_name='floors')
    floor_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Floor number')
    )
    rooms_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(200)],
        verbose_name=_('Number of rooms')
    )
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    gender_type = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        default='female',
        verbose_name=_('Gender type')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Floor {self.floor_number} - {self.dormitory.name}"

    class Meta:
        verbose_name = _('Floor')
        verbose_name_plural = _('Floors')
        ordering = ['dormitory', 'floor_number']
        unique_together = ('dormitory', 'floor_number')


class RoomType(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    capacity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        verbose_name=_('Capacity')
    )
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Price per month'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is active'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.capacity} {_('person(s)')}"

    class Meta:
        verbose_name = _('Room type')
        verbose_name_plural = _('Room types')
        ordering = ['name']


class RoomFacility(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Icon'))
    created_at = models.DateTimeField(auto_now_add=True)  # No default
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Room facility')
        verbose_name_plural = _('Room facilities')
        ordering = ['name']


class Room(models.Model):
    STATUS_CHOICES = (
        ('available', _('Available')),
        ('partially_filled', _('Partially filled')),
        ('full', _('Full')),
        ('under_maintenance', _('Under maintenance'))
    )

    ROOM_TYPE_CHOICES = (
        ('standard', _('Standard')),
        ('improved', _('Improved')),
        ('vip', _('VIP'))
    )

    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE, related_name='rooms')
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='rooms')
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, verbose_name=_('Room type'))
    room_number = models.CharField(max_length=10, verbose_name=_('Room number'))
    facilities = models.ManyToManyField(RoomFacility, blank=True, verbose_name=_('Facilities'))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available',
        verbose_name=_('Status')
    )
    current_occupancy = models.PositiveSmallIntegerField(default=0, verbose_name=_('Current occupancy'))
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Monthly price'))
    room_type_category = models.CharField(
        max_length=20,
        choices=ROOM_TYPE_CHOICES,
        default='standard',
        verbose_name=_('Room type category')
    )
    equipment = models.JSONField(default=dict, blank=True, verbose_name=_('Equipment'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Room {self.room_number} - {self.dormitory.name}"

    class Meta:
        verbose_name = _('Room')
        verbose_name_plural = _('Rooms')
        ordering = ['dormitory', 'floor', 'room_number']
        unique_together = ('dormitory', 'room_number')


class RoomBooking(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled')
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking for {self.room.room_number} by {self.student.username}"
