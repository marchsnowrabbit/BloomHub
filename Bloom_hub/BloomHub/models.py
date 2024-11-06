import json
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager,PermissionsMixin
from django.db import models
from django.forms import JSONField


class BloomUserManager(BaseUserManager):
    def create_user(self, user_id, username, password=None, **extra_fields):
        if not user_id:
            raise ValueError('The User ID is required')
        user = self.model(user_id=user_id, username=username, **extra_fields)
        user.set_password(password)  # 비밀번호 해시화 처리
        user.save(using=self._db)
        return user

    def create_superuser(self, user_id, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(user_id=user_id, username=user_id, email=email, password=password, **extra_fields)

class BloomUser(AbstractBaseUser, PermissionsMixin):
    user_id = models.CharField(max_length=50, unique=True)
    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    youtube_api_key = models.CharField(max_length=255, blank=True, null=True)
    wikifier_api_key = models.CharField(max_length=255, blank=True, null=True)
    profileImg = models.ImageField(upload_to='profiles/', blank=True, null=True)

      # 추가된 필드
    is_staff = models.BooleanField(default=False)  # Staff status
    is_superuser = models.BooleanField(default=False)  # Superuser status

    USERNAME_FIELD = 'user_id'
    REQUIRED_FIELDS = ['email']

    objects = BloomUserManager()

    def __str__(self):
        return self.username
    

################유튜브 영상 DB####################

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class LearningVideo(models.Model):
    vid = models.CharField(max_length=100, unique=True)  # 비디오 ID, 고유
    title = models.CharField(max_length=255)  # 비디오 제목
    setTime = models.IntegerField()  # 비디오 길이 (초 단위)
    uploader = models.CharField(max_length=255, blank=True, null=True)  # 업로더 정보
    view_count = models.IntegerField(default=0)  # 조회수
    std_lang = models.CharField(max_length=10, default="EN")  # 언어 코드 (KR, EN)
    learning_status = models.BooleanField(default=False)  # 학습 상태
    user = models.ForeignKey(
        'BloomUser', 
        on_delete=models.CASCADE, 
        to_field='user_id'  # References the user_id field
    )

class WordData(models.Model):
    video = models.ForeignKey(LearningVideo, to_field='vid', related_name='word_data', on_delete=models.CASCADE)
    word = models.CharField(max_length=255)  # 단어
    pos = models.CharField(max_length=50)  # 품사
    start_time = models.IntegerField()  # 시작 시간 (초 단위)
    end_time = models.IntegerField()  # 종료 시간 (초 단위)
    page_rank = models.FloatField(null=True, blank=True)  # PageRank 점수
    url = models.URLField(null=True, blank=True)  # 관련 URL
    data_type = models.CharField(max_length=10, default="word")  # 데이터 유형

class SentenceData(models.Model):
    video = models.ForeignKey(LearningVideo, to_field='vid', related_name='sentence_data', on_delete=models.CASCADE)
    word = models.TextField()  # 문장
    start_time = models.IntegerField()  # 시작 시간 (초 단위)
    end_time = models.IntegerField()  # 종료 시간 (초 단위)
    data_type = models.CharField(max_length=10, default="sentence")  # 데이터 유형

class AnalysisResult(models.Model):
    video = models.ForeignKey(LearningVideo,to_field='vid',related_name='analysis_results', on_delete=models.CASCADE)
    bloom_stage_segments = models.JSONField()  # 단계별 구간 정보 (예: {"remember": "0-60, 180-240", ...})
    top_nouns = models.JSONField()  # 상위 명사 (예: ["Python", "data", "web", ...])
    donut_chart = models.JSONField()  # Plotly 도넛 차트 JSON 데이터
    dot_chart = models.JSONField()  # Plotly 단계 분포 차트 JSON 데이터
    created_at = models.DateTimeField(auto_now_add=True)


class BloomDictionary(models.Model):
    language = models.CharField(max_length=20)  # 예: 'Korean', 'English'
    stage = models.CharField(max_length=50)  # 예: 'remember', 'understand', 'apply', etc.
    words = models.JSONField()  # 각 단계에 해당하는 단어 목록 (예: ["word1", "word2"])

    class Meta:
        unique_together = ('language', 'stage')  # 언어와 단계가 유일하도록 설정

    def __str__(self):
        return f"{self.language} - {self.stage}"

