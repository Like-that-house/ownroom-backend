from .views import *
from rest_framework import routers
from django.urls import path, include

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
urlpatterns = router.urls

urlpatterns += [
    path('users/signup', RegisterView.as_view()),
    path('users/login', LoginView.as_view()),
]