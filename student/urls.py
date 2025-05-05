from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, ApplicationViewSet, ApplicationDocumentViewSet

router = DefaultRouter()
router.register(r'students', StudentViewSet)
router.register(r'applications', ApplicationViewSet)
router.register(r'application-documents', ApplicationDocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 