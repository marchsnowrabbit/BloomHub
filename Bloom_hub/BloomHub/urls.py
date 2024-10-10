from django.urls import path
from . import views

urlpatterns =[
    path('', views.home, name='home'),  # 메인 홈
    path('login/', views.login_page, name='login'),  # 로그인 페이지
    path('signup/', views.signup_page, name='signup'),  # 회원가입 페이지
    path('guide/', views.guide_page, name='guide'),  # 가이드 페이지
    path('search/', views.search_page, name='search'),  # 검색 페이지
    path('mypage/', views.mypage, name='mypage'),  # 마이페이지
    # 추가 페이지도 여기서 정의
    # 추가된 URL 패턴
    path('learning/', views.learning_page, name='learning'),  # 학습 비디오 페이지
    path('learned/', views.learned_page, name='learned'),  # 학습 완료된 비디오 페이지
    
     # API 경로
    path('check-login/', views.check_login, name='check_login'),  # 로그인 상태 확인
    path('logout/', views.logout_view, name='logout'),  # 로그아웃 처리
]