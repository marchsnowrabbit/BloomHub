"""
URL configuration for tag2 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path         # URL 경로를 정의하기 위해 path 함수를 임포트
from django.shortcuts import render  # Django의 템플릿을 렌더링하기 위한 render 함수를 임포트

from .views import connect_mongo #^ views.py에서 MongoDB와 연결하는 뷰를 가져옴

from .views import signup_view  # ^ views.py에서 사용자 가입을 처리하는 뷰 함수를 가져옴
from .views import home_view    # ^ views.py에서 홈 페이지를 렌더링하는 뷰 함수를 가져옴
from .views import login_view
from . views import logout_view
from django.contrib import admin  #^ Django의 관리 사이트 기능을 사용하기 위한 admin 모듈을 임포트
from . import views
from .views import findID_view, findpwd_view




def render_template(request, template_name):
    """
    주어진 템플릿 이름으로 HTML 페이지를 렌더링하여 반환하는 함수입니다.
    
    :param request: Django의 HttpRequest 객체, 클라이언트의 요청 정보를 포함합니다.
    :param template_name: 렌더링할 템플릿 파일의 이름입니다.
    :return: 렌더링된 HTML 페이지를 포함한 HttpResponse 객체입니다.
    """
    
    
    
    
    return render(request, template_name)


urlpatterns = [

        path('connect-mongo/', connect_mongo, name='connect_mongo'),

    path('admin/', admin.site.urls),
        path('', lambda request: render(request, 'home.html')),  # 루트 URL로 home.html을 렌더링
        path('analysis/', lambda request: render(request, 'analysis.html')),  
        path('Analyze/', lambda request: render(request, 'Analyze.html')),
        path('findID/', findID_view, name='findID'),
        path('reset-password/', findpwd_view, name='findpwd'),
        path('guide/', lambda request: render(request, 'guide.html')),
        # path('home/', lambda request: render(request, 'home.html')),
          





        path('home/', home_view, name='home'),  #^ AJAX 요청을 처리할 뷰 연결
        path('learned/', lambda request: render(request, 'learned.html')),
        path('learning/', lambda request: render(request, 'learning.html')),
       
        # path('loginnew/', lambda request: render(request, 'loginnew.html')),
        path('loginnew/', login_view, name='loginnew'), 
          path('check-login/', views.check_login_view, name='check_login'), #^ 로그인확인 함수
        # path('logout/', logout_view, name='logout'),  # 로그아웃 URL 추가

          
        path('mypage/', lambda request: render(request, 'mypage.html')),
        path('mypagemanager/', lambda request: render(request, 'mypagemanager.html')),
        path('search/', lambda request: render(request, 'search.html')),
        path('searchresult/', lambda request: render(request, 'searchresult.html')),
        # path('', lambda request: render(request, '')),
        # path('signup/', lambda request: render(request, 'signup.html')),  # signup URL로 signup.html을 렌더링    
        path('signup/', signup_view, name='signup'),  #^ AJAX 요청을 처리할 뷰 연결
        path('signup-2/', lambda request: render(request, 'signup-2.html')),  # signup URL로 signup.html을 렌더링



        


]
