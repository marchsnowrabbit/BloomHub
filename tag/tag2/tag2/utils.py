# utils.py

import smtplib
import random

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
