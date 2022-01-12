from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser, PermissionsMixin)
from django.contrib.auth.hashers import *
# Create your models here.


class Base(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, nickname, name, password, phoneNumber):
        if not nickname:
            raise ValueError('Users must have a nickname')
        if not name:
            raise ValueError('Users must have a name')
        if not password:
            raise ValueError('Users must have a password')
        if not phoneNumber:
            raise ValueError('Users must have a phoneNumber')

        user = self.model(
            nickname=nickname,
            name=name,
            phoneNumber=phoneNumber,
          # password=password
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, nickname, name, password, phoneNumber):
        superuser = self.create_user(
            nickname=nickname,
            name=name,
            password=password,
            phoneNumber=phoneNumber
        )
        superuser.is_admin = True
        superuser.is_superuser = True
        superuser.save(using=self._db)
        return superuser


class User(AbstractBaseUser, PermissionsMixin, Base):
    class Meta:
        db_table="user"

    consultantRegisterStatusChoices = [
        ('B', '신청 전'),
        ('R', '신청 후'),
        ('C', '승인 완료')
    ]
    nickname = models.CharField(max_length=50, unique=True, null=False)
    name = models.CharField(max_length=50)
    phoneNumber = models.CharField(max_length=100)
    isConsultant = models.BooleanField(default=False)
    consultantRegisterStatus = models.CharField(max_length=1, choices=consultantRegisterStatusChoices, default='B')
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'nickname'
    REQUIRED_FIELDS = ['name', 'phoneNumber']

    def __str__(self):
        return self.nickname

    @property
    def is_staff(self):
        return self.is_admin

class Portfolio(Base):
    class Meta:
        db_table="portfolio"

    CONCEPT_CHOICES = (
        ('Modern', '모던'),
        ('Minimal', '미니멀'),
        ('Natural', '내추럴'),
        ('Antique', '엔티크'),
        ('NorthEurope', '북유럽')
    )

    CONSULTING_RANGE = (
        ('R', '가구 추천'),
        ('P', '가구 추천부터 배치')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolios')
    title = models.CharField(max_length=100)
    introduction = models.TextField()
    numberOfRooms = models.CharField(max_length=1, choices=(('1','원룸'),('2','투룸'),('3','쓰리룸')))
    floorSpace = models.IntegerField()
    concept = models.CharField(max_length=11, choices=CONCEPT_CHOICES)
    consultingRange = models.CharField(max_length=1, choices=CONSULTING_RANGE)
    description = models.TextField()
    budget = models.IntegerField()
    pricePerUnit = models.IntegerField()

    def __str__(self):
        return 'portfoilo_' + str(self.id)

class Contact(Base):
    class Meta:
        db_table="contact"

    isReported = models.BooleanField(default=False)
    owner = models.ForeignKey(User, related_name='consultants', on_delete=models.CASCADE)
    consultant = models.ForeignKey(User, related_name='owners', on_delete=models.CASCADE)

    def __str__(self):
        return 'contact_' + str(self.id) + '_from_' + str(self.user.nickname) + '_to_' + str(self.consultant.nickname)

class File(Base):
    class Meta:
        db_table="file"

    isReport = models.BooleanField()
    url = models.TextField()
    contact = models.ForeignKey(Contact, related_name='files', on_delete=models.CASCADE)
    filename = models.CharField(max_length=100)

    def __str__(self):
        return 'file_' + str(self.id)

class Image(Base):
    class Meta:
        db_table="image"

    url = models.TextField()
    portfolio = models.ForeignKey(Portfolio, related_name='images', on_delete=models.CASCADE)

    def __str__(self):
        return 'image_' + str(self.id)