"""
URL configuration for joybor project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Define tags for better organization
tags = [
    {'name': 'User Management', 'description': 'User management operations'},
    {'name': 'User Profile Management', 'description': 'User profile management operations'},
    {'name': 'Student Management', 'description': 'Student management operations'},
    {'name': 'Application Management', 'description': 'Application management operations'},
    {'name': 'Application Document Management', 'description': 'Application document management operations'},
    {'name': 'University Management', 'description': 'University management operations'},
    {'name': 'Picture Management', 'description': 'Picture management operations'},
    {'name': 'Dormitory Management', 'description': 'Dormitory management operations'},
    {'name': 'Floor Management', 'description': 'Floor management operations'},
    {'name': 'Room Type Management', 'description': 'Room type management operations'},
    {'name': 'Room Facility Management', 'description': 'Room facility management operations'},
    {'name': 'Room Management', 'description': 'Room management operations'},
    {'name': 'Room Booking Management', 'description': 'Room booking management operations'},
    {'name': 'Payment Type Management', 'description': 'Payment type management operations'},
    {'name': 'Payment Status Management', 'description': 'Payment status management operations'},
    {'name': 'Payment Transaction Management', 'description': 'Payment transaction management operations'},
    {'name': 'Subscription Management', 'description': 'Subscription management operations'},
]

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
   patterns=[
       path('api/users/', include('users.urls')),
       path('api/student/', include('student.urls')),
       path('api/payment/', include('payment.urls')),
       path('api/dormitory/', include('dormitory.urls')),
   ],
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API URLs
    path('api/users/', include('users.urls')),
    path('api/student/', include('student.urls')),
    path('api/payment/', include('payment.urls')),
    path('api/dormitory/', include('dormitory.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
