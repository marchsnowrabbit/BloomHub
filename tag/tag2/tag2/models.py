# myapp/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser


# class User(AbstractUser):
#     wiki_api = models.CharField(max_length=255)
#     youtube_api = models.CharField(max_length=255)
#     watched_videos = models.JSONField(default=list)  # JSON 필드로 시청 기록 저장


#^유저 스키마 모델
class User(models.Model):

    email = models.EmailField(max_length=255, unique=True)  # Email
    password = models.CharField(max_length=128)  # Hashed password
    # join_date = models.DateTimeField(auto_now_add=True)  # Join date
    # name = models.CharField(max_length=255)  # User's name
    # wiki_api = models.CharField(max_length=255)  # Wiki API
    # youtube_api = models.CharField(max_length=255)  # YouTube API

    # Schema for storing watch history
    watched_videos = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.email  # Returns the email when printing the user object
    

    

    