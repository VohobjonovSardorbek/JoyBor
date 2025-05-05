from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UniversityViewSet, PictureViewSet, DormitoryViewSet,
    FloorViewSet, RoomTypeViewSet, RoomFacilityViewSet,
    RoomViewSet, RoomBookingViewSet
)

router = DefaultRouter()
router.register(r'universities', UniversityViewSet)
router.register(r'pictures', PictureViewSet)
router.register(r'dormitories', DormitoryViewSet)
router.register(r'floors', FloorViewSet)
router.register(r'room-types', RoomTypeViewSet)
router.register(r'room-facilities', RoomFacilityViewSet)
router.register(r'rooms', RoomViewSet)
router.register(r'bookings', RoomBookingViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 