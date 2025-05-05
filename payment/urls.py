from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentTypeViewSet, PaymentStatusViewSet,
    PaymentTransactionViewSet, SubscriptionViewSet
)

router = DefaultRouter()
router.register(r'payment-types', PaymentTypeViewSet)
router.register(r'payment-statuses', PaymentStatusViewSet)
router.register(r'transactions', PaymentTransactionViewSet)
router.register(r'subscriptions', SubscriptionViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 