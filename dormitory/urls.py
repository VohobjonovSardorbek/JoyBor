from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UniversityViewSet, PictureViewSet, DormitoryViewSet,
    FloorViewSet, RoomTypeViewSet, RoomFacilityViewSet,
    RoomViewSet, RoomBookingViewSet
)

# Create routers for each endpoint
universities_router = DefaultRouter()
universities_router.register('', UniversityViewSet)

pictures_router = DefaultRouter()
pictures_router.register('', PictureViewSet)

dormitories_router = DefaultRouter()
dormitories_router.register('', DormitoryViewSet)

floors_router = DefaultRouter()
floors_router.register('', FloorViewSet)

room_types_router = DefaultRouter()
room_types_router.register('', RoomTypeViewSet)

room_facilities_router = DefaultRouter()
room_facilities_router.register('', RoomFacilityViewSet)

rooms_router = DefaultRouter()
rooms_router.register('', RoomViewSet)

bookings_router = DefaultRouter()
bookings_router.register('', RoomBookingViewSet)



urlpatterns = [
    # Universities endpoints
    path('universities/', include(universities_router.urls)),
    
    # Pictures endpoints
    path('pictures/', include(pictures_router.urls)),
    
    # Dormitories endpoints
    path('dormitories/', include(dormitories_router.urls)),
    
    # Floors endpoints
    path('floors/', include(floors_router.urls)),
    
    # Room types endpoints
    path('room-types/', include(room_types_router.urls)),
    
    # Room facilities endpoints
    path('room-facilities/', include(room_facilities_router.urls)),
    
    # Rooms endpoints
    path('rooms/', include(rooms_router.urls)),
    
    # Bookings endpoints
    path('bookings/', include(bookings_router.urls)),
] 