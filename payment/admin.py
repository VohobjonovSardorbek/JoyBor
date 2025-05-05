from django.contrib import admin
from .models import PaymentType, PaymentStatus, PaymentTransaction, Subscription

@admin.register(PaymentType)
class PaymentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(PaymentStatus)
class PaymentStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('student', 'dormitory', 'room', 'payment_type', 'amount', 'status', 'payment_date', 'due_date')
    list_filter = ('status', 'payment_type', 'payment_date', 'due_date')
    search_fields = ('student__username', 'dormitory__name', 'room__room_number', 'transaction_id', 'receipt_number')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    raw_id_fields = ('student', 'dormitory', 'room', 'payment_type', 'status', 'created_by')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('dormitory', 'start_date', 'end_date', 'amount', 'payment_status', 'payment_date')
    list_filter = ('payment_status', 'start_date', 'end_date', 'payment_date')
    search_fields = ('dormitory__name', 'receipt_number')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    raw_id_fields = ('dormitory', 'created_by')
