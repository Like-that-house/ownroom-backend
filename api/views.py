from .serializers import *
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, filters

# Create your views here.

User = get_user_model()

JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
JWT_ENCODE_HANDLER = api_settings.JWT_ENCODE_HANDLER

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    queryset = User.objects.all()
    serializer_class = UserSerializer


#회원가입
class RegisterView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            payload = JWT_PAYLOAD_HANDLER(user)
            jwt_token = JWT_ENCODE_HANDLER(payload)
            return Response({"token": jwt_token}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DuplicationCheckView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        nickname = request.data.get("nickname")
        if nickname is not None:
            isDuplicated = User.objects.filter(nickname=nickname).exists()
            return Response(isDuplicated, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class PortfolioFilter(FilterSet):
    concept = filters.CharFilter(field_name='concept')

    class Meta:
        model=Portfolio
        fields=['concept']

class PortfoliosViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PortfolioFilter
