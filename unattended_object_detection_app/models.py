from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator


# Create your models here.

class Upload(models.Model):
    video = models.FileField(upload_to='videos',null=True, validators=[FileExtensionValidator(allowed_extensions=['MOV','avi','mp4','webm','mkv'])])
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)


class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=14)
    date_of_birth = models.DateField()
    place = models.CharField(max_length=20)
    question = models.CharField(max_length=40)