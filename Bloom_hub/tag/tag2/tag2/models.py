# myapp/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser



#^유저 스키마 모델   - DB에 저장될 실제 데이터 이름
class User(models.Model):

    email = models.EmailField(max_length=255, unique=True)  # Email
    password = models.CharField(max_length=128)  # Hashed password
    join_date = models.DateTimeField(auto_now_add=True)  # Join date
    name = models.CharField(max_length=255)  # User's name
    wiki_api = models.CharField(max_length=255)  # Wiki API
    youtube_api = models.CharField(max_length=255)  # YouTube API

    #^ 본  영상
    # watched_videos = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.email  # Returns the email when printing the user object
    



#  User 모델과 ForeignKey 관계를 맺는다. 이 방식은 여러 시청 기록이 유저와 연결
class WatchedVideo(models.Model):
    user = models.ForeignKey(User, related_name="watched_videos", on_delete=models.CASCADE)
    video_id = models.CharField(max_length=255)  # Video ID (e.g., YouTube video ID)
    title = models.CharField(max_length=255)  # Video title
    watched_at = models.DateTimeField(auto_now_add=True)  # Timestamp for when video was watched

    def __str__(self):
        return f"{self.user.email} watched {self.title}"
    

    