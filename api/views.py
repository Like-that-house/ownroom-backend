from .serializers import *
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, filters
import boto3
from ownroom.settings import *
from django.http import FileResponse, HttpResponse
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
import mimetypes

# Create your views here.

User = get_user_model()

JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
JWT_ENCODE_HANDLER = api_settings.JWT_ENCODE_HANDLER

JWT_DECODE_HANDLER = api_settings.JWT_DECODE_HANDLER
JWT_PAYLOAD_GET_USER_ID_HANDLER = api_settings.JWT_PAYLOAD_GET_USER_ID_HANDLER

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

class ConsultingApplicationDownloadView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = (JSONWebTokenAuthentication,)

    def post(self, request):
        # 현재 로그인한 계정의 userId를 불러옴
        jwt_value = JSONWebTokenAuthentication().get_jwt_value(request)
        payload = JWT_DECODE_HANDLER(jwt_value)
        userId = JWT_PAYLOAD_GET_USER_ID_HANDLER(payload)

        # 유저의 isConsultant 조회
        user = get_object_or_404(User, id=userId)
        isConsultant = user.isConsultant

        # body로 넘겨받은 userId를 조회
        data = JSONParser().parse(request)
        opponentUserId = data['userId']

        if isConsultant:
            # 현재 컨설턴트 일 때
            contact = get_object_or_404(Contact, consultant_id=userId, owner_id=opponentUserId)
        else:
            # 현재 오너 일 때
            contact = get_object_or_404(Contact, owner_id=userId, consultant_id=opponentUserId )

        # 컨설팅 신청서(isReport = False)
        file = contact.files.get(isReport=False)
        url = file.url
        filename = file.filename

        # s3에서 파일 다운로드
        client = boto3.client('s3')
        client.download_file(AWS_STORAGE_BUCKET_NAME, url, 'media/'+filename)

        # 파일 Reponse
        with open('media/'+filename, 'rb') as fh:
            mime_type, _ = mimetypes.guess_type('media/'+filename)
            response = HttpResponse(fh.read(), content_type=mime_type)
            response['Content-Disposition'] = 'attachment;filename*=UTF-8\'\'%s' % filename
            os.remove('media/'+filename)
            return response

class ConsultingReportDownloadView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = (JSONWebTokenAuthentication,)

    def post(self, request):
        # 현재 로그인한 계정의 userId를 불러옴
        jwt_value = JSONWebTokenAuthentication().get_jwt_value(request)
        payload = JWT_DECODE_HANDLER(jwt_value)
        userId = JWT_PAYLOAD_GET_USER_ID_HANDLER(payload)

        # 유저의 isConsultant 조회
        user = get_object_or_404(User, id=userId)
        isConsultant = user.isConsultant

        # body로 넘겨받은 userId를 조회
        data = JSONParser().parse(request)
        opponentUserId = data['userId']

        if isConsultant:
            # 현재 컨설턴트 일 때
            contact = get_object_or_404(Contact, consultant_id=userId, owner_id=opponentUserId)
        else:
            # 현재 오너 일 때
            contact = get_object_or_404(Contact, owner_id=userId, consultant_id=opponentUserId )

        # 컨설팅 보고서(isReport = True)
        file = contact.files.get(isReport=True)
        url = file.url
        filename = file.filename

        # s3에서 파일 다운로드
        client = boto3.client('s3')
        client.download_file(AWS_STORAGE_BUCKET_NAME, url, 'media/'+filename)

        # 파일 Reponse
        with open('media/'+filename, 'rb') as fh:
            mime_type, _ = mimetypes.guess_type('media/'+filename)
            response = HttpResponse(fh.read(), content_type=mime_type)
            response['Content-Disposition'] = 'attachment;filename*=UTF-8\'\'%s' % filename
            os.remove('media/'+filename)
            return response

class DownloadTest(APIView):
    permission_classes = (AllowAny,)
    def get(self, request):
        with open('media/테스트.docx', 'rb') as fh:
            mime_type,_ = mimetypes.guess_type('media/테스트.docx')
            response = HttpResponse(fh.read(), content_type=mime_type)
            response['Content-Disposition'] = 'attachment;filename*=UTF-8\'\'%s' % '테스트.docx'
            #os.remove('media/테스트.docx')
            return response