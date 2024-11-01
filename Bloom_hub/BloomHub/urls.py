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


    #############로그인 관련 urls###############
    path('login/', views.login_view, name='login'),
    path('login/kor/', views.login_kor, name='loginkor'),
    path('logout/', views.logout_view, name='logout_view'),
    path('signup/', views.signup_view, name='signup'),
    path('signup/kor/', views.signup_kor, name='signupkor'),
    path('check-duplicate/', views.check_duplicate, name='check_duplicate'),
    path('check-login/', views.check_login, name='check_login'),
    #################################################

    path('mypage/', views.mypage, name='mypage'),
    path('mypage/kor/', views.mypage_kor, name='mypagekor'),
    path('mypage/manager/', views.mypage_manager, name='mypage_manager'),
    
    path('search', views.search, name='search'),  # 슬래시 없이 URL 작성
    path('search/result', views.search_result, name='searchresult'),
    path('search/result/kor', views.search_result_kor, name='searchresultkor'),
    path('study/<str:video_id>', views.study, name='study'),  # video_id를 인자로 받는 study URL

    path('find-id/', views.find_id, name='findID'),
    path('find-id/kor/', views.find_id_kor, name='find_id_kor'),

    path('find-pwd/', views.find_pwd, name='findpwd'),
    path('find-pwd/kor/', views.find_pwd_kor, name='find_pwd_kor'),

    path('analysis/', views.analysis, name='analysis'),
]
