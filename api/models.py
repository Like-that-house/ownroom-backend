from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser, PermissionsMixin)

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
            password=password
        )
        #user.set_password(password)
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

    objects = UserManager()

    USERNAME_FIELD = 'nickname'
    REQUIRED_FIELDS = ['name', 'phoneNumber']

    def __str__(self):
        return self.nickname

    @property
    def is_staff(self):
        return self.is_admin