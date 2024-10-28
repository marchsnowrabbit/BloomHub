import json
from pyexpat.errors import messages
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib.auth.hashers import make_password
from django.core.files.images import ImageFile
from django.views.decorators.csrf import csrf_exempt
import os

@csrf_exempt  
def signup_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        # 폼 데이터
        user_id = data.get('user_id')
        password = data.get('password')
        password2 = data.get('password2')  # 비밀번호 확인 추가
        email = data.get('email')
        username = data.get('username')
        youtube_api_key = data.get('youtube_api_key')
        wikifier_api_key = data.get('wikifier_api_key')
        profile_image = request.FILES.get('profile_image') if 'profile_image' in request.FILES else None

        # 아이디 중복 확인
        if User.objects.filter(username=user_id).exists():
            return JsonResponse({'success': False, 'message': '이미 존재하는 아이디입니다.'})

        # 비밀번호 조건 확인
        if not any(char.isupper() for char in password) or not any(not char.isalnum() for char in password):
            return JsonResponse({'success': False, 'message': '비밀번호에는 대문자와 특수문자가 각각 하나 이상 필요합니다.'})

        # 비밀번호 일치 확인
        if password != password2:
            return JsonResponse({'success': False, 'message': '비밀번호가 일치하지 않습니다.'})

        # 프로필 이미지가 없으면 기본 이미지 설정
        if not profile_image:
            default_image_path = os.path.join('static', 'img', 'profile.png')
            profile_image = ImageFile(open(default_image_path, 'rb'))

        # User 객체 생성
        user = User.objects.create(
            username=user_id,
            email=email,
            password=make_password(password),
            first_name=username
        )

        # UserProfile 모델에 추가 정보 저장
        user.youtube_api_key = youtube_api_key
        user.wikifier_api_key = wikifier_api_key
        user.profile_image = profile_image
        user.save()  # 사용자 정보 저장

        login(request, user)
        return JsonResponse({'success': True})

    return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, '로그인 실패: 잘못된 사용자명 또는 비밀번호.')
            return redirect('login')
    return render(request, 'login.html')

def check_login_view(request):
    if request.user.is_authenticated:
        return JsonResponse({'loggedIn': True})
        
    else:
        return JsonResponse({'loggedIn': False})
def check_session(request):
    # 세션 체크 로직
    if request.user.is_authenticated:  # 사용자 인증 상태 체크
        return JsonResponse({'status': 'success', 'user': request.user.username})
    else:
        return JsonResponse({'status': 'failure', 'message': 'User is not authenticated.'})    


# 나머지 뷰 함수들은 그대로 유지
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

def search_page(request):
    return render(request, 'search.html')

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

def logout(request):
    request.session.flush()
    return redirect('home')
