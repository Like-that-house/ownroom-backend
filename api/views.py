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
from .s3utils import s3client
import urllib

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

class MyInfoView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication,)
    def get(self, request):
        jwt_value = JSONWebTokenAuthentication().get_jwt_value(request)
        payload = JWT_DECODE_HANDLER(jwt_value)
        userId = JWT_PAYLOAD_GET_USER_ID_HANDLER(payload)

        user = User.objects.get(id=userId)
        serializer = UserSerializer(user)
        return Response(serializer.data)


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


class UserSwitchView(APIView):
    def patch(self, request):
        user = request.user
        # owner->consultant. 컨설턴트 승인 완료 상태(C)인 경우에만 전환 가능
        switchTo = request.data.get("switchTo")
        if switchTo=='consultant':
            if user.consultantRegisterStatus=='B' or user.consultantRegisterStatus=='R':
                return Response({"message":"컨설턴트 승인 후 전환 가능합니다."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                user.isConsultant = True
                user.save()
                return Response({"message":"컨설턴트로 전환합니다."}, status=status.HTTP_200_OK)
        #consultant->owner
        else:
            user.isConsultant = False
            user.save()
            return Response({"message":"고객으로 전환합니다."}, status=status.HTTP_200_OK)


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
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication,)

    def get(self, request):
        # 현재 로그인한 계정의 userId를 불러옴
        jwt_value = JSONWebTokenAuthentication().get_jwt_value(request)
        payload = JWT_DECODE_HANDLER(jwt_value)
        userId = JWT_PAYLOAD_GET_USER_ID_HANDLER(payload)

        # 유저의 isConsultant 조회
        user = get_object_or_404(User, id=userId)
        isConsultant = user.isConsultant

        # body로 넘겨받은 userId를 조회
        opponent = User.objects.get(nickname=self.request.query_params.get('nickname'))

        if isConsultant:
            # 현재 컨설턴트 일 때
            contact = get_object_or_404(Contact, consultant_id=userId, owner=opponent)
        else:
            # 현재 오너 일 때
            contact = get_object_or_404(Contact, owner_id=userId, consultant=opponent)

        # 컨설팅 신청서(isReport = False)
        file = contact.files.get(isReport=False)
        url = file.url
        filename = file.filename

        # s3에서 파일 다운로드
        client = boto3.client('s3')
        client.download_file(AWS_STORAGE_BUCKET_NAME, url, 'media/'+filename)

        # 다운로드 url return
        return Response({"url": "https://api.ownroom.link/api/consultings/downloadUrl?filename={}".format(filename)},status=status.HTTP_200_OK)

class ConsultingReportDownloadView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = (JSONWebTokenAuthentication,)

    def get(self, request):
        # 현재 로그인한 계정의 userId를 불러옴
        jwt_value = JSONWebTokenAuthentication().get_jwt_value(request)
        payload = JWT_DECODE_HANDLER(jwt_value)
        userId = JWT_PAYLOAD_GET_USER_ID_HANDLER(payload)

        # 유저의 isConsultant 조회
        user = get_object_or_404(User, id=userId)
        isConsultant = user.isConsultant

        # query parameter로 넘겨받은 nickname으로 user 조회
        opponent = User.objects.get(nickname=self.request.query_params.get('nickname'))

        if isConsultant:
            # 현재 컨설턴트 일 때
            contact = get_object_or_404(Contact, consultant_id=userId, owner=opponent)
        else:
            # 현재 오너 일 때
            contact = get_object_or_404(Contact, owner_id=userId, consultant=opponent)

        # 컨설팅 보고서(isReport = True)
        file = contact.files.get(isReport=True)
        url = file.url
        filename = file.filename

        # s3에서 파일 다운로드
        client = boto3.client('s3')
        client.download_file(AWS_STORAGE_BUCKET_NAME, url, 'media/'+filename)

        # 다운로드 url return
        return Response({"url": "https://api.ownroom.link/api/consultings/downloadUrl?filename={}".format(filename)}, status=status.HTTP_200_OK)

class DownloadView(APIView):
    permission_classes = (AllowAny,)
    def get(self, request):
        filename = request.GET['filename']
        with open('media/'+filename, 'rb') as fh:
            mime_type,_ = mimetypes.guess_type('media/'+filename)
            response = HttpResponse(fh.read(), content_type=mime_type)
            quote_file_name = urllib.parse.quote(filename.encode('utf-8'))
            response['Content-Disposition'] = 'attachment;filename*=UTF-8\'\'%s' % quote_file_name
            os.remove('media/'+filename)
            return response

class DownloadTest(APIView):
    permission_classes = (AllowAny,)
    def get(self, request):
        with open('media/컨설팅_보고서_이소이.docx', 'rb') as fh:
            mime_type,_ = mimetypes.guess_type('media/컨설팅_보고서_이소이.docx')
            response = HttpResponse(fh.read(), content_type=mime_type)
            response['Content-Disposition'] = 'attachment;filename*=UTF-8\'\'%s' % '컨설팅_보고서_이소이.docx'
            #os.remove('media/테스트.docx')
            return response


class FileUploadView(APIView):
    def get_user(self, nickname):
        user = get_object_or_404(User, nickname=nickname)
        return user

    def post(self, request, format=None):
        user = request.user
        filename = request.FILES['file']  # filename
        target = request.POST['nickname']
        # targetId = request.data.get("nickname")
        target = self.get_user(nickname=target)
        urlpath = s3client.upload(filename)

        if urlpath is None:
            return Response({"message": "파일 업로드 실패"}, status=status.HTTP_400_BAD_REQUEST)

        # 컨설팅 보고서 작성
        if user.isConsultant:
            contact = get_object_or_404(Contact, owner=target, consultant=user)
            file = File(
                contact=contact,
                url=urlpath,
                filename=filename,
                isReport=True
            )
            file.save()
            contact.isReported = True
            contact.save()
            return Response({"message": "컨설팅 보고서가 업로드되었습니다."}, status=status.HTTP_200_OK)
        # 컨설팅 신청서 작성
        else:
            contact = Contact(
                owner=user,
                consultant=target
            )
            contact.save()
            file = File(
                contact=Contact.objects.latest('id'),
                url=urlpath,
                filename=filename,
                isReport=False
            )
            file.save()
            return Response({"message": "컨설팅 신청서가 업로드되었습니다."}, status=status.HTTP_200_OK)


class MyConsultingView(APIView):
    def get(self, request):
        user = request.user
        #consultant인 경우
        if user.isConsultant:
            contact = Contact.objects.filter(consultant=user)
            serializer = ContactSerializer(contact, many=True)
            return Response(serializer.data)
        #owner인 경우
        else:
            contact = Contact.objects.filter(owner=user)
            serializer = ContactSerializer(contact, many=True)
            return Response(serializer.data)


