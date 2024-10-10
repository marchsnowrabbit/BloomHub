from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def login_page(request):
    return render(request, 'loginnew.html')

def signup_page(request):
    return render(request, '회원가입newnew.html')

def guide_page(request):
    return render(request, 'guide.html')

def search_page(request):
    return render(request, 'search.html')

def mypage(request):
    return render(request, 'mypage.html')

def learning_page(request):
    return render(request, 'learning.html')

def learned_page(request):
    return render(request, 'learned.html')

# 로그인 상태 확인 API
def check_login(request):
    if request.user.is_authenticated:
        return JsonResponse({'loggedIn': True})
    return JsonResponse({'loggedIn': False})

# 로그아웃 API
def logout_view(request):
    logout(request)
    return JsonResponse({'success': True})

# 나머지 페이지들도 비슷한 방식으로 추가
