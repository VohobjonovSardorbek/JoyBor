from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User
from dormitory.models import Dormitory, Room


# Create your models here.

class PaymentType(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Amount'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is active'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.amount}"

    class Meta:
        verbose_name = _('Payment type')
        verbose_name_plural = _('Payment types')


class PaymentStatus(models.Model):
    name = models.CharField(max_length=50, verbose_name=_('Name'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Payment status')
        verbose_name_plural = _('Payment statuses')


class PaymentTransaction(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', _('Cash')),
        ('card', _('Card')),
        ('bank_transfer', _('Bank Transfer')),
        ('mobile_payment', _('Mobile Payment')),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE, related_name='payments')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.ForeignKey(PaymentType, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Amount'))
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name=_('Payment method')
    )
    status = models.ForeignKey(PaymentStatus, on_delete=models.CASCADE)
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        verbose_name=_('Transaction ID')
    )
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Payment date'))
    due_date = models.DateField(verbose_name=_('Due date'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    receipt_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name=_('Receipt number')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_payments',
        verbose_name=_('Created by')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.student.username} - {self.amount}"

    class Meta:
        verbose_name = _('Payment transaction')
        verbose_name_plural = _('Payment transactions')
        ordering = ['-payment_date']


class Subscription(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('paid', _('Paid')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    ]

    dormitory = models.ForeignKey(Dormitory, on_delete=models.CASCADE, related_name='subscriptions')
    start_date = models.DateField(verbose_name=_('Start date'))
    end_date = models.DateField(verbose_name=_('End date'))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Amount'))
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name=_('Payment status')
    )
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Payment date'))
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentTransaction.PAYMENT_METHOD_CHOICES,
        blank=True,
        null=True,
        verbose_name=_('Payment method')
    )
    receipt_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name=_('Receipt number')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_subscriptions',
        verbose_name=_('Created by')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Subscription for {self.dormitory.name} - {self.start_date} to {self.end_date}"

    class Meta:
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')
        ordering = ['-created_at']
