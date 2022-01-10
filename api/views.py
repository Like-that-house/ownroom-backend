from .serializers import *
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.filters import OrderingFilter

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


class PortfolioViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    filter_backends = [DjangoFilterBackend,]
    filter_fields = ['concept']

# owner가 신청서를 보내면 contact table에 먼저 행 추가 -> file table에 신청서 url 업로드(user의 isConsultant 값에 따라 isReport 변경)
# consultant가 보고서를 보내면 file table에 보고서 업로드(해당 user, consultant에 해당하는 contact table 참조)

# file upload test
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
            consultant = user
            owner = target
            isReport = True
        else:
            owner = user
            consultant = target
            isReport = False

        contact = Contact(
            owner = owner,
            consultant = consultant
        )
        contact.save()

        file = File(
            contact = Contact.objects.latest('id'),
            url = file_url,
            isReport = isReport
        )
        file.save()

        return Response({"message": "file uploaded"}, status=status.HTTP_200_OK)