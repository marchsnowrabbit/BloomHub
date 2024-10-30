from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

class BloomUserManager(BaseUserManager):
    def create_user(self, user_id, username, password=None, **extra_fields):
        if not user_id:
            raise ValueError('The User ID is required')
        user = self.model(user_id=user_id, username=username, **extra_fields)
        user.set_password(password)  # 비밀번호 해시화 처리
        user.save(using=self._db)
        return user

class BloomUser(AbstractBaseUser):
    user_id = models.CharField(max_length=50, unique=True)
    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    youtube_api_key = models.CharField(max_length=255, blank=True, null=True)
    wikifier_api_key = models.CharField(max_length=255, blank=True, null=True)
    profileImg = models.ImageField(upload_to='profiles/', blank=True, null=True)

    USERNAME_FIELD = 'user_id'
    REQUIRED_FIELDS = ['email']

    objects = BloomUserManager()

    def __str__(self):
        return self.username

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
