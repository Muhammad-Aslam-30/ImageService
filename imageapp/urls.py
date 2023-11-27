from django.urls import path, include
from rest_framework import routers
from .views import ImageViewSet, RegisterAPI, LoginAPI

router = routers.DefaultRouter()
router.register(r'images', ImageViewSet, basename='image')

urlpatterns = [
    path('api/image', ImageViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}), name='image-retrieve-and-delete'),
    path('api/', include(router.urls)),
    path('register/', RegisterAPI.as_view()),
    path('login/', LoginAPI.as_view()),
]