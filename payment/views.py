from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import PaymentType, PaymentStatus, PaymentTransaction, Subscription
from .serializers import (
    PaymentTypeSerializer, PaymentStatusSerializer,
    PaymentTransactionSerializer, PaymentTransactionCreateSerializer, PaymentTransactionUpdateSerializer,
    SubscriptionSerializer, SubscriptionCreateSerializer, SubscriptionUpdateSerializer
)
from users.models import User
from .permissions import IsSuperAdmin, IsDormitoryAdmin, IsStudent
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(
    tags=['/api/payment/payment-types/'],
    operation_description="Payment type management endpoints",
    responses={
        200: openapi.Response(
            description="Success",
            schema=PaymentTypeSerializer
        )
    }
)
class PaymentTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing payment types.
    """
    queryset = PaymentType.objects.all()
    serializer_class = PaymentTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return PaymentType.objects.none()
        return PaymentType.objects.filter(is_active=True)

@swagger_auto_schema(
    tags=['/api/payment/payment-statuses/'],
    operation_description="Payment status management endpoints",
    responses={
        200: openapi.Response(
            description="Success",
            schema=PaymentStatusSerializer
        )
    }
)
class PaymentStatusViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing payment statuses.
    """
    queryset = PaymentStatus.objects.all()
    serializer_class = PaymentStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

@swagger_auto_schema(
    tags=['/api/payment/transactions/'],
    operation_description="Payment transaction management endpoints",
    responses={
        200: openapi.Response(
            description="Success",
            schema=PaymentTransactionSerializer
        )
    }
)
class PaymentTransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing payment transactions.
    """
    queryset = PaymentTransaction.objects.all()
    serializer_class = PaymentTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentTransactionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PaymentTransactionUpdateSerializer
        return PaymentTransactionSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return PaymentTransaction.objects.none()
        user = self.request.user
        if user.is_super_admin:
            return PaymentTransaction.objects.all()
        elif user.is_dormitory_admin:
            return PaymentTransaction.objects.filter(dormitory__admin=user)
        return PaymentTransaction.objects.filter(student__user=user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @swagger_auto_schema(
        operation_description="Process a payment",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['amount', 'payment_type'],
            properties={
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                'payment_type': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        ),
        responses={
            201: openapi.Response(
                description="Payment processed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'student': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'payment_type': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    @action(detail=False, methods=['post'])
    def process_payment(self, request):
        serializer = PaymentTransactionSerializer(data=request.data)
        if serializer.is_valid():
            transaction = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Get user's payment history",
        responses={
            200: openapi.Response(
                description="Payment history retrieved successfully",
                schema=PaymentTransactionSerializer(many=True)
            )
        }
    )
    @action(detail=False, methods=['get'])
    def my_payments(self, request):
        transactions = self.get_queryset()
        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get payment statistics",
        responses={
            200: openapi.Response(
                description="Payment statistics",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'total_transactions': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'pending_payments': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'paid_payments': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'failed_payments': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'payment_type_stats': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                        'status_stats': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        user = request.user
        queryset = self.get_queryset()
        
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date and end_date:
            queryset = queryset.filter(payment_date__range=[start_date, end_date])
        
        # Calculate statistics
        total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0
        total_transactions = queryset.count()
        pending_payments = queryset.filter(status__name='pending').count()
        paid_payments = queryset.filter(status__name='paid').count()
        failed_payments = queryset.filter(status__name='failed').count()
        
        # Group by payment type
        payment_type_stats = queryset.values('payment_type__name').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        # Group by status
        status_stats = queryset.values('status__name').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        return Response({
            'total_amount': total_amount,
            'total_transactions': total_transactions,
            'pending_payments': pending_payments,
            'paid_payments': paid_payments,
            'failed_payments': failed_payments,
            'payment_type_stats': payment_type_stats,
            'status_stats': status_stats
        })

    @swagger_auto_schema(
        operation_description="Get upcoming payments",
        responses={
            200: openapi.Response(
                description="List of upcoming payments",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'due_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                            'status': openapi.Schema(type=openapi.TYPE_OBJECT),
                        }
                    )
                )
            )
        }
    )
    @action(detail=False, methods=['get'])
    def upcoming_payments(self, request):
        user = request.user
        queryset = self.get_queryset()
        
        # Get payments due in the next 7 days
        upcoming_date = timezone.now() + timedelta(days=7)
        upcoming_payments = queryset.filter(
            due_date__lte=upcoming_date,
            status__name='pending'
        ).order_by('due_date')
        
        serializer = self.get_serializer(upcoming_payments, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get overdue payments",
        responses={
            200: openapi.Response(
                description="List of overdue payments",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'due_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                            'status': openapi.Schema(type=openapi.TYPE_OBJECT),
                        }
                    )
                )
            )
        }
    )
    @action(detail=False, methods=['get'])
    def overdue_payments(self, request):
        user = request.user
        queryset = self.get_queryset()
        
        # Get overdue payments
        overdue_payments = queryset.filter(
            due_date__lt=timezone.now(),
            status__name='pending'
        ).order_by('due_date')
        
        serializer = self.get_serializer(overdue_payments, many=True)
        return Response(serializer.data)

@swagger_auto_schema(
    tags=['/api/payment/subscriptions/'],
    operation_description="Subscription management endpoints",
    responses={
        200: openapi.Response(
            description="Success",
            schema=SubscriptionSerializer
        )
    }
)
class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing subscriptions.
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

    def get_serializer_class(self):
        if self.action == 'create':
            return SubscriptionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SubscriptionUpdateSerializer
        return SubscriptionSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Subscription.objects.none()
        user = self.request.user
        if user.is_super_admin:
            return Subscription.objects.all()
        elif user.is_dormitory_admin:
            return Subscription.objects.filter(dormitory__admin=user)
        return Subscription.objects.filter(student__user=user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @swagger_auto_schema(
        operation_description="Get active subscriptions",
        responses={
            200: openapi.Response(
                description="List of active subscriptions",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'student': openapi.Schema(type=openapi.TYPE_OBJECT),
                            'start_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                            'end_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                            'status': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
                )
            )
        }
    )
    @action(detail=False, methods=['get'])
    def active_subscriptions(self, request):
        subscriptions = self.get_queryset().filter(payment_status='paid')
        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update subscription payment status",
        request_body=SubscriptionUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Subscription status updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'payment_status': openapi.Schema(type=openapi.TYPE_STRING),
                        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    @action(detail=True, methods=['post'])
    def update_payment_status(self, request, pk=None):
        subscription = self.get_object()
        serializer = SubscriptionUpdateSerializer(subscription, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Get subscription statistics",
        responses={
            200: openapi.Response(
                description="Subscription statistics",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'total_subscriptions': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'active_subscriptions': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'expiring_soon': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'status_stats': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        user = request.user
        queryset = self.get_queryset()
        
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date and end_date:
            queryset = queryset.filter(start_date__range=[start_date, end_date])
        
        # Calculate statistics
        total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0
        total_subscriptions = queryset.count()
        active_subscriptions = queryset.filter(
            payment_status='paid',
            end_date__gt=timezone.now()
        ).count()
        expiring_soon = queryset.filter(
            payment_status='paid',
            end_date__lte=timezone.now() + timedelta(days=30),
            end_date__gt=timezone.now()
        ).count()
        
        # Group by payment status
        status_stats = queryset.values('payment_status').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        return Response({
            'total_amount': total_amount,
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'expiring_soon': expiring_soon,
            'status_stats': status_stats
        })

    @swagger_auto_schema(
        operation_description="Get subscriptions expiring soon",
        responses={
            200: openapi.Response(
                description="List of subscriptions expiring soon",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'student': openapi.Schema(type=openapi.TYPE_OBJECT),
                            'end_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                            'status': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
                )
            )
        }
    )
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        user = request.user
        queryset = self.get_queryset()
        
        # Get subscriptions expiring in the next 30 days
        expiring_date = timezone.now() + timedelta(days=30)
        expiring_subscriptions = queryset.filter(
            end_date__lte=expiring_date,
            end_date__gt=timezone.now(),
            payment_status='paid'
        ).order_by('end_date')
        
        serializer = self.get_serializer(expiring_subscriptions, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Cancel a subscription",
        responses={
            200: openapi.Response(
                description="Subscription cancelled successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'student': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'dormitory': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'start_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                        'end_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        subscription = self.get_object()
        subscription.status = 'cancelled'
        subscription.save()
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)
