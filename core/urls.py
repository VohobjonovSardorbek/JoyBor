from django.contrib import admin
from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import token_obtain_pair, token_refresh
from django.conf import settings
from django.conf.urls.static import static


from main.views import DormitoryListAPIView, UniversityListAPIView, DormitoryCreateAPIView, UniversityDetailApiView, \
    UniversityCreateAPIView, DormitoryDetailAPIView, FloorListAPIView, FloorCreateAPIView, FloorDetailAPIView, \
    RoomListAPIView, RoomCreateAPIView, RoomDetailAPIView, StudentListAPIView, StudentCreateAPIView, \
    StudentDetailAPIView, ApplicationListAPIView, ApplicationCreateAPIView, ApplicationDetailAPIView, \
    PaymentListAPIView, PaymentCreateAPIView, PaymentDetailAPIView, UserListAPIView, UserDetailAPIView, \
    UserCreateAPIView, ProvinceListAPIView, DistrictListAPIView, DormitoryImageListAPIView, DormitoryImageDetailAPIView, \
    DormitoryImageCreateAPIView

schema_view = get_schema_view(
    openapi.Info(
        title="Joy Bor API",
        default_version='v1',
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),
]

urlpatterns += [
    path('users/', UserListAPIView.as_view(), name='user-list'),
    path('user/create/', UserCreateAPIView.as_view(), name='user-create'),
    path('users/<int:pk>/', UserDetailAPIView.as_view(), name='user-detail'),

    path('universities/', UniversityListAPIView.as_view(), name='university-list'),
    path('university/create/', UniversityCreateAPIView.as_view(), name='university-create'),
    path('universities/<int:pk>/', UniversityDetailApiView.as_view(), name='university-detail'),

    path('dormitories/', DormitoryListAPIView.as_view(), name='dormitory-list'),
    path('dormitory/create/', DormitoryCreateAPIView.as_view(), name='dormitory-create'),
    path('dormitories/<int:pk>/', DormitoryDetailAPIView.as_view(), name='dormitory-detail'),

    path('floors/', FloorListAPIView.as_view(), name='floor-list'),
    path('floor/create/', FloorCreateAPIView.as_view(), name='floor-create'),
    path('floors/<int:pk>/', FloorDetailAPIView.as_view(), name='floor-detail'),

    path('rooms/', RoomListAPIView.as_view(), name='room-list'),
    path('room/create/', RoomCreateAPIView.as_view(), name='room-create'),
    path('rooms/<int:pk>/', RoomDetailAPIView.as_view(), name='room-detail'),

    path('students/', StudentListAPIView.as_view(), name='student-list'),
    path('student/create/', StudentCreateAPIView.as_view(), name='student-create'),
    path('students/<int:pk>/', StudentDetailAPIView.as_view(), name='student-detail'),

    path('applications/', ApplicationListAPIView.as_view(), name='application-list'),
    path('application/create/', ApplicationCreateAPIView.as_view(), name='application-create'),
    path('applications/<int:pk>/', ApplicationDetailAPIView.as_view(), name='application-detail'),

    path('payments/', PaymentListAPIView.as_view(), name='payment-list'),
    path('payment/create/', PaymentCreateAPIView.as_view(), name='payment-create'),
    path('payments/<int:pk>/', PaymentDetailAPIView.as_view(), name='payment-detail'),

    path('provinces/', ProvinceListAPIView.as_view(), name='province-list'),
    path('districts/', DistrictListAPIView.as_view(), name='district-list'),

    path('dormitory_images/', DormitoryImageListAPIView.as_view(), name='dormitory-image-list'),
    path('dormitory_image_create', DormitoryImageCreateAPIView.as_view(), name='dormitory-image-create'),
    path('dormitory_images/<int:pk>/', DormitoryImageDetailAPIView.as_view(), name='dormitory-image-detail'),
]

urlpatterns += [
    path('token/', token_obtain_pair),
    path('token/refresh/', token_refresh),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

