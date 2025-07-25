from django.contrib import admin
from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import token_obtain_pair, token_refresh
from django.conf import settings
from django.conf.urls.static import static

from main.views import *

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
    path('register/', StudentRegisterCreateAPIView.as_view()),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),

    path('users/', UserListAPIView.as_view(), name='user-list'),
    path('user/create/', UserCreateAPIView.as_view(), name='user-create'),
    path('users/<int:pk>/', UserDetailAPIView.as_view(), name='user-detail'),

    path('universities/', UniversityListAPIView.as_view(), name='university-list'),
    path('university/create/', UniversityCreateAPIView.as_view(), name='university-create'),
    path('universities/<int:pk>/', UniversityDetailApiView.as_view(), name='university-detail'),

    path('dormitories/', DormitoryListAPIView.as_view(), name='dormitory-list'),
    path('my-dormitory/', MyDormitoryAPIView.as_view(), name='my-dormitory'),
    path('my-dormitory-update/', MyDormitoryUpdateAPIView.as_view(), name='my-dormitory-update'),
    path('dormitory/create/', DormitoryCreateAPIView.as_view(), name='dormitory-create'),
    path('dormitories/<int:pk>/', DormitoryDetailAPIView.as_view(), name='dormitory-detail'),

    path('floors/', FloorListAPIView.as_view(), name='floor-list'),
    path('available-floors/', AvailableFloorsAPIView.as_view(), name='available-floors'),
    path('floor/create/', FloorCreateAPIView.as_view(), name='floor-create'),
    path('floors/<int:pk>/', FloorDetailAPIView.as_view(), name='floor-detail'),

    path('rooms/', RoomListAPIView.as_view(), name='room-list'),
    path('every-available-rooms/', EveryAvailableRoomsAPIView.as_view(), name='available-rooms'),
    path('available-rooms/', AvailableRoomsAPIView.as_view(), name='available-rooms'),
    path('room/create/', RoomCreateAPIView.as_view(), name='room-create'),
    path('rooms/<int:pk>/', RoomDetailAPIView.as_view(), name='room-detail'),

    path('students/', StudentListAPIView.as_view(), name='student-list'),
    path('export-student/', ExportStudentExcelAPIView.as_view(), name='export-student'),
    path('student/create/', StudentCreateAPIView.as_view(), name='student-create'),
    path('students/<int:pk>/', StudentDetailAPIView.as_view(), name='student-detail'),

    path('applications/', ApplicationListAPIView.as_view(), name='application-list'),
    path('application/create/', ApplicationCreateAPIView.as_view(), name='application-create'),
    path('applications/<int:pk>/', ApplicationDetailAPIView.as_view(), name='application-detail'),

    path('payments/', PaymentListAPIView.as_view(), name='payment-list'),
    path('export-payment/', ExportPaymentExcelAPIView.as_view(), name='export-payment'),
    path('payment/create/', PaymentCreateAPIView.as_view(), name='payment-create'),
    path('payments/<int:pk>/', PaymentDetailAPIView.as_view(), name='payment-detail'),

    path('provinces/', ProvinceListAPIView.as_view(), name='province-list'),
    path('districts/', DistrictListAPIView.as_view(), name='district-list'),
    path('dashboard/', AdminDashboardAPIView.as_view(), name='dashboard'),

    path('dormitory_images/', DormitoryImageListAPIView.as_view(), name='dormitory-image-list'),
    path('dormitory_image_create', DormitoryImageCreateAPIView.as_view(), name='dormitory-image-create'),
    path('dormitory_images/<int:pk>/', DormitoryImageDetailAPIView.as_view(), name='dormitory-image-detail'),

    path('monthly_revenue/', MonthlyRevenueAPIView.as_view(), name='monthly-revenue'),
    path('room_status_stats/', RoomStatusStatsAPIView.as_view(), name='room-status-stats'),

    path('tasks/', TasksListCreateAPIView.as_view(), name='task-list'),
    path('tasks/<int:pk>/', TaskDetailAPIView.as_view(), name='task-detail'),
    path('recent_activity/', RecentActivityAPIView.as_view(), name='recent-activity'),

    path('register/tenant/', TenantRegisterAPIView.as_view(), name='tenant-register'),

    path('apartments/', ApartmentListAPIView.as_view(), name='apartment-list'),
    path('apartments/<int:pk>/', ApartmentDetailAPIView.as_view(), name='apartment-detail'),
    path('apartments/create/', ApartmentCreateAPIView.as_view(), name='apartment-create'),
    path('apartments/<int:pk>/update/', ApartmentUpdateAPIView.as_view(), name='apartment-update'),

    # path('amenities/', AmenityListAPIView.as_view(), name='amenity-list'),
    # path('amenities/create/', AmenityCreateAPIView.as_view(), name='amenity-create'),
    # path('amenities/<int:pk>/update/', AmenityUpdateAPIView.as_view(), name='amenity-update'),
    # path('amenities/<int:pk>/delete/', AmenityDeleteAPIView.as_view(), name='amenity-delete'),

    path('rules/', RuleListAPIView.as_view(), name='rule-list'),
    path('rules/create/', RuleCreateAPIView.as_view(), name='rule-create'),
    # path('rules/<int:pk>/', RetrieveUpdateDestroyAPIView.as_view(), name='rule-detail'),

    path('answers/', AnswerForApplicationListApiview.as_view(), name='answer-list'),
    path('answers/<int:pk>/', AnswerForApplicationDetailAPIView.as_view(), name='answer-detail'),
    path('answers/create/', AnswerForApplicationCreateAPIView.as_view(), name='answer-create'),
    path('answers/<int:pk>/update/', AnswerForApplicationUpdateAPIView.as_view(), name='answer-update'),
    path('answers/<int:pk>/delete/', AnswerForApplicationDeleteAPIView.as_view(), name='answer-delete'),
]


urlpatterns += [
path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
path('token/refresh/', token_refresh),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
