import email
from django.contrib import messages
from pyexpat.errors import messages
from telnetlib import LOGOUT
from django.forms import PasswordInput
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.hashers import make_password
from BloomHub.models import User

# Create your views here.

# 로그인 부분 수정 -> 지금 안 됨

def home(request):
    return render(request, 'home.html')

def home_kor_view(request):
    return render(request, 'homekor.html')

def hi_view(request):
    return render(request, 'hi.html') 

def login_view(request):
    return render(request, 'loginnew.html')

def login_kor_view(request):
    return render(request, 'loginkor.html')

def guide_view(request):
    return render(request, 'guide.html')

def guide_kor_view(request):
    return render(request, 'guidekor.html')

def search_view(request):
    return render(request, 'search.html')

def search_kor_view(request):
    return render(request, 'searchkor.html')

def mypage_view(request):
    return render(request, 'mypage.html')

def mypage_kor_view(request):
    return render(request, 'mypagekor.html')

def signup_view(request):
    return render(request, 'signup.html')

def signup_kor_view(request):
    return render(request, 'signupkor.html')

def learning_view(request):
    return render(request, 'learning.html')

def learned_view(request):
    return render(request, 'learned.html')

def check_login(request):
    if request.user.is_authenticated:
        return redirect('home') 
    else:
        return redirect('login')

def logout_view(request):
    LOGOUT(request) 
    return redirect('home')

def learning_kor_view(request):
    return render(request, 'learningkor.html')

def learned_kor_view(request):
    return render(request, 'learnedkor.html')

def findID_kor_view(request):
    return render(request, 'findIDkor.html')

def findID_view(request):
    return render(request, 'findID.html')

def findpwd_view(request):
    return render(request, 'findpwd.html')

def findpwd_kor_view(request):
    return render(request, 'findpwdkor.html')

from django.shortcuts import render

def searchResult_view(request):
    search_query = request.GET.get('searchResult', '')  
    search_results = []  # 검색 결과 추가하기

    return render(request, 'searchresult.html', {'search_query': search_query, 'search_results': search_results})

def searchResult_kor_view(request):
    search_query = request.GET.get('searchResult', '')  
    search_results = []  # 검색 결과 추가하기

    return render(request, 'searchresultkor.html', {'search_query': search_query, 'search_results': search_results})

def analysis_view(request):
    return render(request, 'analysis.html')

def signup(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        username = request.POST.get('username')

        # 로그 추가
        print(f"회원가입 시도: 이메일 - {email}, 사용자 이름 - {username}")

        if User.objects.filter(email=email).exists():
            messages.error(request, '이미 등록된 이메일입니다.')
            return redirect('signup')

        hashed_password = make_password(password)
        user = User(email=email, password=hashed_password, username=username)
        user.save()
        messages.success(request, '회원가입이 완료되었습니다.')
        return redirect('login')
    
    return render(request, 'signup.html')

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)

            if check_password(password, user.password):  # 해싱된 비밀번호와 비교
                request.session['user_id'] = user.id  # 세션에 사용자 ID 저장
                return redirect('home')
            else:
                messages.error(request, '비밀번호가 일치하지 않습니다.')
        except User.DoesNotExist:
            messages.error(request, '존재하지 않는 사용자입니다.')

    return render(request, 'loginnew.html')

def register_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not User.objects.filter(username=username).exists():
            user = User(username=username, password=password)  
            user.save()
            return JsonResponse({'success': True, 'message': '가입 완료'})
        else:
            return JsonResponse({'success': False, 'message': '이미 존재하는 아이디입니다.'})


