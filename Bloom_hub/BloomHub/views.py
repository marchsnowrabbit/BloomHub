import os
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from googleapiclient.discovery import build
import isodate
from .models import BloomUser

logger = logging.getLogger(__name__)

class YoutubeVideoapi:
    import os

class YoutubeVideoapi:
    def __init__(self):
        # 환경 변수에서 API 키를 불러오거나 명시적으로 키를 설정합니다.
        self.developer_key = os.getenv('YOUTUBE_API_KEY', 'AIzaSyA7Qn-gNPnDQ4xgpDemtU0OzArCzL0zqvI')
        self.youtube_api_service_name = "youtube"
        self.youtube_api_version = 'v3'
        
        # YouTube API 호출 로직

    def videolist(self, keyword):
        youtube = build(self.youtube_api_service_name, self.youtube_api_version, developerKey=self.developer_key)
        
        try:
            search_response = youtube.search().list(
                q=keyword,
                order='viewCount',
                part='snippet',
                maxResults=20
            ).execute()

            video_ids = []
            videos = []
            for item in search_response['items']:
                video_id = item['id'].get('videoId')
                if video_id:
                    video_ids.append(video_id)
                    videos.append({
                        'title': item['snippet']['title'],
                        'videoId': video_id,
                        'thumbnail': item['snippet']['thumbnails']['default']['url'],
                        'channelTitle': item['snippet']['channelTitle']
                    })

            if video_ids:
                videos_response = youtube.videos().list(
                    id=','.join(video_ids),
                    part='contentDetails,statistics'
                ).execute()

                for i, video in enumerate(videos_response['items']):
                    duration = self.convert_duration(video['contentDetails']['duration'])
                    view_count = video['statistics'].get('viewCount', 0)
                    videos[i]['duration'] = duration
                    videos[i]['viewCount'] = view_count

            return videos

        except Exception as e:
            logger.error(f"오류 발생: {e}")
            return []

    def convert_duration(self, duration):
        duration_obj = isodate.parse_duration(duration)
        total_minutes = int(duration_obj.total_seconds() // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}시간 {minutes}분" if hours > 0 else f"{minutes}분"

# 검색 페이지 뷰
def search(request):
    if request.method == 'POST':
        keyword = request.POST.get('keyword', '')
        video_api = YoutubeVideoapi()
        videos = video_api.videolist(keyword)

        if not videos:
            messages.error(request, '비디오를 찾을 수 없습니다.')

        return render(request, 'searchresult.html', {'videos': videos, 'keyword': keyword})
    return render(request, 'search.html')

# 중복 체크 API 뷰
def check_duplicate(request):
    field = request.GET.get('field')
    value = request.GET.get('value')
    
    logger.info(f"Received check_duplicate request with field: {field}, value: {value}")

    if not field or not value:
        logger.error("필드 또는 값이 전달되지 않았습니다.")
        return JsonResponse({'error': '필드 또는 값이 전달되지 않았습니다.'}, status=400)

    if field == 'user_id':
        exists = bool(BloomUser.objects.filter(user_id=value).values('user_id').first())
    elif field == 'email':
        exists = bool(BloomUser.objects.filter(email=value).values('email').first())
    else:
        logger.error("잘못된 필드가 요청되었습니다.")
        return JsonResponse({'error': '잘못된 필드입니다.'}, status=400)

    return JsonResponse({'exists': exists})

# 회원가입 뷰
def signup_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        username = request.POST.get('username')
        password = request.POST.get('password1')
        password_confirm = request.POST.get('password2')
        email = request.POST.get('email')
        youtube_api_key = request.POST.get('youtube_api_key')
        wikifier_api_key = request.POST.get('wikifier_api_key')

        logger.info(f"Signup attempt: user_id={user_id}, email={email}")

        if password != password_confirm:
            messages.error(request, "비밀번호가 일치하지 않습니다.")
            return render(request, 'signup.html')

        hashed_password = make_password(password)

        try:
            user = BloomUser.objects.create(
                user_id=user_id,
                username=username,
                email=email,
                password=hashed_password,
                youtube_api_key=youtube_api_key,
                wikifier_api_key=wikifier_api_key,
            )
            messages.success(request, "회원가입이 완료되었습니다.")
            logger.info("User created successfully.")
            return redirect('login')
        except Exception as e:
            logger.error(f"오류가 발생했습니다: {e}")
            messages.error(request, f"오류가 발생했습니다: {str(e)}")

    return render(request, 'signup.html')

# 로그인 뷰
def login_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        password = request.POST.get('password')

        try:
            user = BloomUser.objects.get(user_id=user_id)
        except BloomUser.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'user_id'})

        if user.check_password(password):
            login(request, user)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'password'})

    return render(request, 'login.html')

# 로그인 상태 확인 API 뷰
def check_login(request):
    is_logged_in = request.user.is_authenticated
    username = request.user.username if is_logged_in else ""
    return JsonResponse({'is_logged_in': is_logged_in, 'username': username})

# 로그아웃 뷰
def logout_view(request):
    logout(request)
    return redirect('home')

# 페이지 렌더링 뷰들
def home(request):
    return render(request, 'home.html')

def home_kor(request):
    return render(request, 'homekor.html')

def guide(request):
    return render(request, 'guide.html')

def guide_kor(request):
    return render(request, 'guidekor.html')

def learning(request):
    return render(request, 'learning.html')

def learning_kor(request):
    return render(request, 'learningkor.html')

def learned(request):
    return render(request, 'learned.html')

def learned_kor(request):
    return render(request, 'learnedkor.html')

def login_page(request):
    return render(request, 'login.html')

def login_kor(request):
    return render(request, 'loginkor.html')

def signup_page(request):
    return render(request, 'signup.html')

def signup_kor(request):
    return render(request, 'signupkor.html')

def mypage(request):
    return render(request, 'mypage.html')

def mypage_kor(request):
    return render(request, 'mypagekor.html')

def mypage_manager(request):
    return render(request, 'mypagemanager.html')

def search_kor(request):
    return render(request, 'searchkor.html')

def search_result(request):
    return render(request, 'searchresult.html')

def search_result_kor(request):
    return render(request, 'searchresultkor.html')

def find_id(request):
    return render(request, 'findID.html')

def find_id_kor(request):
    return render(request, 'findIDkor.html')

def find_pwd(request):
    return render(request, 'findpwd.html')

def find_pwd_kor(request):
    return render(request, 'findpwdkor.html')

def analysis(request):
    return render(request, 'analysis.html')
