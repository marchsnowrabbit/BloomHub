from django.urls import path
from . import views  # views 모듈을 임포트하여 사용

urlpatterns = [
    path('', views.home, name='home'),  # index를 search로 변경
    path('kor/', views.home_kor, name='homekor'),

    path('guide/', views.guide, name='guide'),
    path('guide/kor/', views.guide_kor, name='guidekor'),

    path('learning/', views.learning, name='learning'),
    path('learning/kor/', views.learning_kor, name='learningkor'),

    path('learned/', views.learned, name='learned'),
    path('learned/kor/', views.learned_kor, name='learnedkor'),

    path('login/', views.login_page, name='login'),
    path('login/kor/', views.login_kor, name='loginkor'),
    path('check-login/', views.check_login_view, name='check_login'),
    path('logout/', views.logout, name='logout'),
    path('check-session/', views.check_session, name='check_session'),

    path('signup/', views.signup_page, name='signup'),
    path('signup/kor/', views.signup_kor, name='signupkor'),

    path('mypage/', views.mypage, name='mypage'),
    path('mypage/kor/', views.mypage_kor, name='mypagekor'),
    path('mypage/manager/', views.mypage_manager, name='mypage_manager'),

    path('search/', views.search, name='search'),
    path('search/kor/', views.search_kor, name='searchkor'),

    path('search/result/', views.search_result, name='searchresult'),
    path('search/result/kor/', views.search_result_kor, name='searchresultkor'),

    path('find-id/', views.find_id, name='findID'),
    path('find-id/kor/', views.find_id_kor, name='find_id_kor'),

    path('find-pwd/', views.find_pwd, name='findpwd'),
    path('find-pwd/kor/', views.find_pwd_kor, name='find_pwd_kor'),

    path('analysis/', views.analysis, name='analysis'),
]
