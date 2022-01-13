from .views import *
from rest_framework import routers
from django.urls import path, include

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'portfolios', PortfoliosViewSet, basename='portfolio')
urlpatterns = router.urls

urlpatterns += [
    path('users/signup', RegisterView.as_view()),
    path('users/login', LoginView.as_view()),
    path('users/check', DuplicationCheckView.as_view()),
]