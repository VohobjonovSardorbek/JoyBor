from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from .views import UserViewSet, UserProfileViewSet

# Swagger schema
schema_view = get_schema_view(
   openapi.Info(
      title="Joy Bor API",
      default_version='v1',
      description="Yotoqxonalar platformasining API hujjatlari",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="info@joybor.com"),
      license=openapi.License(name="MIT License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'profiles', UserProfileViewSet)

urlpatterns = [
    path('docs/', schema_view.as_view(), name='swagger'),
    path('', include(router.urls)),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
