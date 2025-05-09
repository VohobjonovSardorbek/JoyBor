from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


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
