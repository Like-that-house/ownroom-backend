from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.auth import get_user_model
from .models import *
from .validators import validate_phone
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

# JWT 사용을 위한 설정
JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
JWT_ENCODE_HANDLER = api_settings.JWT_ENCODE_HANDLER

User = get_user_model()

# 회원가입
class UserSerializer(serializers.ModelSerializer):
    consultantRegisterStatus = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'nickname', 'name', 'phoneNumber', 'isConsultant', 'consultantRegisterStatus', 'password']

    def validate(self, data):
        password = data.get('password')
        phoneNumber = data.get('phoneNumber')
        if validate_password(password):
            raise serializers.ValidationError(detail=True)
        if not validate_phone(phoneNumber):
            raise serializers.ValidationError("Invalid phone number")
        return data

    def create(self, validated_data):
        user = User(
            nickname=validated_data.get("nickname"),
            name=validated_data.get("name"),
            phoneNumber=validated_data.get("phoneNumber"),
        )
        user.set_password(validated_data.get("password"))
        user.save()
        return user

    def get_consultantRegisterStatus(self, obj):
        return obj.get_consultantRegisterStatus_display()

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
            raise serializers.ValidationError('Invalid user')
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
        model = Image
        fields = [
            'id',
            'url'
        ]

class PortfolioSerializer(serializers.ModelSerializer):
    # Nested Serializer
    images = ImageSerializer(source='image_set', many=True, read_only=True)

    # Serializer Method Field
    user = serializers.SerializerMethodField()
    concept = serializers.SerializerMethodField()
    consultingRange = serializers.SerializerMethodField()

    def get_user(self, obj):
        return {"nickname": obj.user.nickname}

    def get_concept(self, obj):
        return obj.get_concept_display()

    def get_consultingRange(self, obj):
        return obj.get_consultingRange_display()

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


class ContactSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    consultant = serializers.SerializerMethodField()
    class Meta:
        model = Contact
        fields = ['owner', 'owner', 'isReported', 'created_date']

    def get_owner(self, obj):
        return obj.owner.nickname

    def get_consultant(self, obj):
        return obj.consultant.nickname

