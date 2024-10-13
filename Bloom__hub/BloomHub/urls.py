from django.urls import path
from .views import home
from . import views

urlpatterns = [
    path('', home, name='home'), 
    path('kor/', views.home_kor_view, name='homekor'),
    path('hi/', views.hi_view, name='hi'),
    path('login/', views.login_view, name='login'),
    path('login/kor/', views.login_kor_view, name='loginkor'),
    path('signup/', views.signup_view, name='signup'),
    path('signup/kor/', views.signup_kor_view, name='signupkor'),
    path('learning/', views.learning_view, name='learning'),
    path('learning/kor/', views.learning_kor_view, name='learningkor'),
    path('learned/', views.learning_view, name='learned'),
    path('learned/kor/', views.learning_kor_view, name='learnedkor'),
    path('check-login/', views.check_login, name='check_login'),
    path('logout/', views.logout_view, name='logout'),
    path('guide/', views.guide_view, name='guide'),
    path('guide/kor/', views.guide_kor_view, name='guidekor'),
    path('search/', views.search_view, name='search'),
    path('search/kor/', views.search_kor_view, name='searchkor'),
    path('mypage/', views.mypage_view, name='mypage'),
    path('mypage/kor/', views.mypage_kor_view, name='mypagekor'),
    path('findID/', views.findID_view, name='findID'),
    path('findID/kor/', views.findID_kor_view, name='findIDkor'),
    path('findpwd', views.findpwd_view, name='findpwd'),
    path('findpwd/kor/', views.findpwd_kor_view, name='findpwdkor'),
    path('search/result/', views.searchResult_view, name='searchresult'),
    path('search/result/kor/', views.searchResult_kor_view, name='searchresultkor'),
    path('analysis/', views.analysis_view, name='analysis'), 
]
