from .views import *
from rest_framework import routers
from django.urls import path
from . import views

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = router.urls

urlpatterns = router.urls

urlpatterns += [
    path('consulting/application', views.FileUploadView.as_view()),
    path('consulting/report', views.FileUploadView.as_view()),
    path('users/login', views.LoginView.as_view()),
]
