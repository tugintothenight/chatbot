from django.db import models
from django.contrib.auth.models import User


class Document(models.Model):
    description = models.CharField(max_length=255, blank=True)
    document = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)


class Answer(models.Model):
    answer_at = models.DateTimeField(auto_now_add=True)
    answer_content = models.TextField()
    ask_at = models.DateTimeField(auto_now_add=True)
    ask_content = models.TextField()
    uploaded_file = models.FileField(upload_to='')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

# class Account(models.Model):
#     id = models.AutoField(primary_key=True)
#     username = models.CharField(max_length=150, unique=True)
#     date_joined = models.DateTimeField(auto_now_add=True)
#     is_active = models.BooleanField(default=True)
#     is_staff = models.BooleanField(default=False)
#     is_superuser = models.BooleanField(default=False)

