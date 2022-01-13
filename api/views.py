from .serializers import *
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, filters
from .utils import s3client

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


class FileUploadView(APIView):
    def get_user(self, id):
        user = get_object_or_404(User, pk=id)
        return user

    def post(self, request, format=None):
        user = request.user
        filename = request.FILES['file']  # filename
        targetId = request.POST['id']
        # targetId = request.data.get("userId")
        target = self.get_user(id=targetId)
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