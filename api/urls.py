from .views import *
from rest_framework import routers
from django.urls import path, include
from . import views

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
urlpatterns = router.urls

urlpatterns += [
    path('users/signup', RegisterView.as_view()),
]