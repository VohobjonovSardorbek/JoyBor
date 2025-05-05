from rest_framework import serializers
from .models import PaymentType, PaymentStatus, PaymentTransaction, Subscription
from users.serializers import UserSerializer
from dormitory.serializers import DormitorySerializer, RoomSerializer

class PaymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentType
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class PaymentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentStatus
        fields = '__all__'

class PaymentTransactionSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    dormitory = DormitorySerializer(read_only=True)
    room = RoomSerializer(read_only=True)
    payment_type = PaymentTypeSerializer(read_only=True)
    status = PaymentStatusSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')

class PaymentTransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = [
            'student', 'dormitory', 'room', 'payment_type',
            'amount', 'payment_method', 'status', 'due_date',
            'description'
        ]
        extra_kwargs = {
            'student': {'required': True},
            'dormitory': {'required': True},
            'room': {'required': True},
            'payment_type': {'required': True},
            'amount': {'required': True},
            'payment_method': {'required': True},
            'status': {'required': True},
            'due_date': {'required': True}
        }

class PaymentTransactionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = ['status', 'description', 'receipt_number']
        extra_kwargs = {
            'status': {'required': True},
            'description': {'required': False},
            'receipt_number': {'required': False}
        }

class SubscriptionSerializer(serializers.ModelSerializer):
    dormitory = DormitorySerializer(read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')

class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            'dormitory', 'start_date', 'end_date', 'amount',
            'payment_method'
        ]
        extra_kwargs = {
            'dormitory': {'required': True},
            'start_date': {'required': True},
            'end_date': {'required': True},
            'amount': {'required': True},
            'payment_method': {'required': True}
        }

class SubscriptionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['payment_status', 'payment_date', 'receipt_number']
        extra_kwargs = {
            'payment_status': {'required': True},
            'payment_date': {'required': False},
            'receipt_number': {'required': False}
        } 