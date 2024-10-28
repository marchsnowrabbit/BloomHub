from django.contrib.auth.models import AbstractUser
from django.db import models

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    user_id = models.CharField(max_length=255, unique=True)  # user_id 필드 추가
    youtube_api_key = models.CharField(max_length=255, blank=True)
    wikifier_api_key = models.CharField(max_length=255, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=False)
    # first_name, last_name 필드 제거
    first_name = None
    last_name = None

# # 유튜브 비디오 모델 정의
# class YouTubeVideo(models.Model):
#     link = models.URLField()
#     title = models.CharField(max_length=200)
#     channel_name = models.CharField(max_length=100)
#     duration = models.PositiveIntegerField()  # 영상 길이 (초 단위)
#     is_learned = models.BooleanField(default=False)

# # 학습된 비디오 모델 정의
# class LearnedVideo(models.Model):
#     youtube_video = models.ForeignKey(YouTubeVideo, on_delete=models.CASCADE)
#     subtitle_language = models.CharField(max_length=10, choices=[('KR', '한국어'), ('EN', '영어')])
#     nouns = models.JSONField()  # 명사 5개
#     bloom_sections = models.JSONField()  # Bloom 단계별 구간 리스트
#     plotly_graphs = models.JSONField()  # Plotly 그래프 2종
