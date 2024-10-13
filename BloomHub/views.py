from telnetlib import LOGOUT
from django.shortcuts import redirect, render

# Create your views here.

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

