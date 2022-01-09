from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.auth import get_user_model
from .models import *

# JWT 사용을 위한 설정
JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
JWT_ENCODE_HANDLER = api_settings.JWT_ENCODE_HANDLER

User = get_user_model()

# 회원가입
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'nickname', 'name', 'phoneNumber', 'isConsultant']


class LoginBackend(ModelBackend): # 준환님 readme.md 참고. 이거 안하면 계속 userid=None 나옴..
    def authenticate(self, request, nickname=None, password=None, **kwargs):
        try:
            user = User.objects.get(nickname=nickname)
            print(user)
            if user.check_password(password):
                #if user.password == password:
                return user
            return None

        except User.DoesNotExist:
            return None


# 로그인
class UserLoginSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=150, write_only=True)
    token = serializers.CharField(max_length=255, read_only=True)

    class Meta:
        model = User
        fields = ['nickname', 'password', 'token']

    def validate(self, data):
        nickname = data.get("nickname", None)
        password = data.get("password", None)
        user = authenticate(nickname=nickname, password=password)

        if user is None:
            return {'nickname': 'None'} # password가 안맞아도 해당 에러.
        try:
            payload = JWT_PAYLOAD_HANDLER(user)
            jwt_token = JWT_ENCODE_HANDLER(payload)
            update_last_login(None, user)

        except User.DoesNotExist:
            raise serializers.ValidationError(
                'User does not exist'
            )
        return {
            'nickname': user.nickname,
            'token': jwt_token
        }

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        models = Image
        fields = [
            'id',
            'url'
        ]

class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = [
            'id',
            'title',
            'introduction',
            'numberOfRooms',
            'floorSpace',
            'concept',
            'consultingRange',
            'description',
            'budget',
            'pricePerUnit',
            'images',
            'user'
        ]

        # Nested Serializer
        images = ImageSerializer(source='image_set', many=True, read_only=True)

        # Serializer Method Field
        user = serializers.SerializerMethodField()

        def get_user(self, obj):
            return {"nickname": obj.user.nickname}
