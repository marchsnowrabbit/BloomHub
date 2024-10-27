from django.http import JsonResponse  # JSON 응답을 반환하기 위한 JsonResponse 클래스를 임포트
from django.views.decorators.csrf import csrf_exempt  # CSRF 보호를 우회할 수 있는 데코레이터를 임포트
from django.utils.decorators import method_decorator  # 메서드 데코레이터를 사용하기 위한 모듈을 임포트
import json  # JSON 데이터 처리 기능을 사용하기 위한 모듈을 임포트

from .models import User  # ^  Django에서 정의한 사용자 모델을 임포트

from mongoengine import Document, StringField  # ^  MongoDB 문서 모델링에 사용
from pymongo import MongoClient  #^ MongoDB와 상호작용하기 위해 MongoClient 클래스를 임포트

import bcrypt  # 비밀번호 해싱 및 검증을 위한 bcrypt 라이브러리를 임포트

from django.contrib.auth.hashers import make_password  # 비밀번호를 해싱하기 위한 make_password 함수를 임포트
from django.shortcuts import render  #^ 템플릿을 렌더링하기 위한 render 함수를 임포트

from django.shortcuts import redirect
import random
import smtplib


from .utils import send_verification_code  # send_verification_code 함수 임포트



""" 이부분 수정 해야할 수도  """
# from django.conf import settings
# from django.contrib.auth import get_user_model

# User = get_user_model()  # 커스텀 사용자 모델을 가져오는 방법
""" 이부분 수정 해야할 수도  """


#^  몽고 db서버와 연결 
def connect_mongo():
    client = MongoClient('mongodb://127.0.0.1:27017/magatia')
    db = client['magatia']  # 데이터베이스 선택
    return db


# ^ MongoEngine 모델 정의
class UserProfile(Document):
    username = StringField(required=True)
    email = StringField(required=True, unique=True)
    password = StringField(required=True)


""" utils.py 에 있는 함수로 쓸 수도 있음 """
def send_verification_code(email):
    # 이메일로 인증번호 발송 (SMTP 사용 예시)
    code = random.randint(100000, 999999)  # 6자리 랜덤 숫자 생성
    subject = '인증번호입니다'
    message = f'당신의 인증번호는 {code}입니다.'
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('your_email@gmail.com', 'your_email_password')
            server.sendmail('your_email@gmail.com', email, f'Subject: {subject}\n\n{message}')
    except Exception as e:
        print(f'이메일 전송 오류: {e}')
    
    return code




def findID_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            code = send_verification_code(email)
            return JsonResponse({'success': True, 'code': code, 'message': '인증번호가 발송되었습니다.'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': '해당 이메일은 존재하지 않습니다.'})

    return render(request, 'findID.html')




def findpwd_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        new_password = request.POST.get('new_password')
        try:
            user = User.objects.get(email=email)
            user.password = new_password  # 비밀번호는 해시화하여 저장
            user.save()
            return JsonResponse({'success': True, 'message': '비밀번호가 변경되었습니다.'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': '해당 이메일은 존재하지 않습니다.'})

    return render(request, 'findpwd.html')




#? 회원가입 처리 함수
def signup(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')

            # 이메일 중복 체크 (MongoEngine 사용)
            if UserProfile.objects(email=email).first():
                return JsonResponse({'success': False, 'message': 'Email already in use.'})

            # 비밀번호 암호화
            hashed_password = make_password(password)

            # MongoDB에 사용자 정보 저장
            user_profile = UserProfile(username=email, email=email, password=hashed_password)
            user_profile.save()

            return JsonResponse({'success': True, 'message': 'Signup successful!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})



@csrf_exempt
def login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

        try:
            user = User.objects.get(email=email)
            if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                request.session['user_id'] = user.id  # 세션에 사용자 ID 저장
                return JsonResponse({'success': True, 'message': '로그인 되었습니다.'}, status=200)
            else:
                return JsonResponse({'success': False, 'message': '비밀번호가 잘못되었습니다.'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'}, status=404)

    return JsonResponse({'success': False, 'message': 'POST 요청만 허용됩니다.'}, status=405)





@csrf_exempt
def save_watched_video(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        video_id = data.get('videoId')
        title = data.get('title')
        user_id = request.session.get('user_id')

        if user_id is None:
            return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'}, status=401)

        user = User.objects.get(id=user_id)
        user.watched_Videos.append({'videoId': video_id, 'title': title})
        user.save()

        return JsonResponse({'success': True, 'message': '시청 기록이 저장되었습니다.'})

    return JsonResponse({'success': False, 'message': 'POST 요청만 허용됩니다.'}, status=405)

@csrf_exempt
def get_watched_videos(request):
    if request.method == 'GET':
        user_id = request.session.get('user_id')

        if user_id is None:
            return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'}, status=401)

        user = User.objects.get(id=user_id)
        return JsonResponse({'success': True, 'watchedVideos': user.watchedVideos}, status=200)

    return JsonResponse({'success': False, 'message': 'GET 요청만 허용됩니다.'}, status=405)






#^ 회원가입 페이지를 렌더링하는 뷰
def signup_view(request):
    if request.method == 'POST':
        # ?AJAX 요청 처리
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')

            # 이메일과 비밀번호가 모두 제공되었는지 확인
            if email and password:
                    # 이미 존재하는 이메일인지 확인
                    if User.objects.filter(email=email).exists():
                     return JsonResponse({'success': False, 'message': '이미 존재하는 이메일입니다.'})
                     #^ 사용자를 데이터베이스에 저장
                    user = User(email=email, password=make_password(password))  # 비밀번호 해싱
                    user.save()  #^ 데이터베이스에 저장

                    return JsonResponse({'success': True, 'message': '회원가입에 성공했습니다.'})

            return JsonResponse({'success': False, 'message': '이메일과 비밀번호를 모두 입력하세요.'})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': '유효하지 않은 JSON 형식입니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    # GET 요청 시 회원가입 페이지를 렌더링
    return render(request, 'signup.html')  # signup.html 파일을 렌더링




# 홈 페이지를 렌더링하는 뷰
def home_view(request):

# 세션에 'user' 키가 있는지 확인하여 로그인 상태 확인
    if 'user' in request.session:
        logged_in = True
       
    else:
          logged_in = False

 
                
     # 로그인 상태를 템플릿에 전달
    return render(request, 'home.html', {'loggedIn': logged_in})



#임시
def login_view (request) : 

    # 로그인 로직
    if request.method == 'POST':
       if request.user.is_authenticated:
            return redirect('home')  # 홈으로 리다이렉트
    return render (request ,'loginnew.html')






def check_login_view(request):
    if request.user.is_authenticated:
        return JsonResponse({'loggedIn': True})
        
    else:
        return JsonResponse({'loggedIn': False})
    


def logout_view(request):
    # 세션에서 'user' 키를 삭제하여 로그아웃 처리
    if 'user' in request.session:
        del request.session['user']
    return redirect('home')  # 홈 페이지로 리디렉션