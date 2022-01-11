from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from .serializers import *
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404
from .storages import *

# Create your views here.

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    queryset = User.objects.all()
    serializer_class = UserSerializer


class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# owner가 신청서를 보내면 contact table에 먼저 행 추가 -> file table에 신청서 url 업로드(user의 isConsultant 값에 따라 isReport 변경)
# consultant가 보고서를 보내면 file table에 보고서 업로드(해당 user, consultant에 해당하는 contact table 참조)

# 컨설팅 신청서 업로드 api/consulting/application
class ApplicatoinUploadView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self, id):
        user = get_object_or_404(User, pk=id)
        return user

    def post(self, request, format=None):
        user = request.user
        file = request.FILES['file']
        targetId = request.POST['id']  # value값 그대로 넘어옴.
        target = self.get_object(id=targetId)
        file_url = FileUpload(s3_client).upload(file)

        if user.isConsultant:
            Response({"message":"고객으로 전환 후 이용 가능합니다."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            contact = Contact(
                owner=user,
                consultant=target
            )
            contact.save()

            file = File(
                contact = Contact.objects.latest('id'),
                url = file_url,
                isReport = False
            )
            file.save()

            return Response({"message": "Application file is uploaded"}, status=status.HTTP_200_OK)

# 컨설팅 보고서 업로드 api/consulting/report
class ReportUploadView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self, id):
        user = get_object_or_404(User, pk=id)
        return user

    def post(self, request, format=None):
        user = request.user
        file = request.FILES['file']
        targetId = request.POST['id']  # value값 그대로 넘어옴.
        target = self.get_object(id=targetId)
        file_url = FileUpload(s3_client).upload(file)

        if user.isConsultant==False:
            Response({"message": "컨설턴트 전환 후 이용 가능합니다."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            file = File(
                contact=Contact.objects.get(owner=target, consultant=user),
                url=file_url,
                isReport=True
            )
            file.save()

            return Response({"message": "Report file is uploaded"}, status=status.HTTP_200_OK)

# 파일 업로드 하나로 합침.
class FileUploadView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self, id):
        user = get_object_or_404(User, pk=id)
        return user

    def post(self, request, format=None):
        user = request.user
        file = request.FILES['file'] # filename
        targetId = request.POST['id'] # value값 그대로 넘어옴.
        target = self.get_object(id=targetId)
        file_url = FileUpload(s3_client).upload(file)

        if user.isConsultant:
            try:
                contact = Contact.objects.get(owner=target, consultant=user)
            except ObjectDoesNotExist:
                raise Http404();

            file = File(
                contact = contact,
                url=file_url,
                isReport=True
            )
            file.save()
            return Response({"message": "Report file is uploaded"}, status=status.HTTP_200_OK)
        else:
            contact = Contact(
                owner = user,
                consultant = target
            )
            contact.save()
            file = File(
                contact = Contact.objects.latest('id'),
                url = file_url,
                isReport = False
            )
            file.save()
            return Response({"message": "Application file is uploaded"}, status=status.HTTP_200_OK)