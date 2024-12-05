# BloomScope 🌱  
**Cognitive Stage Auto-Tagging for YouTube Videos**  

<img width="1276" alt="image (1)" src="https://github.com/user-attachments/assets/11ba1264-1092-4539-a3b1-115bdafb33a1">

BloomScope is a tool that analyzes YouTube video subtitles to automatically tag them according to Bloom's Taxonomy cognitive stages. Built with Django and MongoDB, it leverages NLP techniques and GPT models to optimize video content for educational purposes.



[![Velog's GitHub stats](https://velog-readme-stats.vercel.app/api?name=marchsnowrabbit)](https://velog.io/@marchsnowrabbit)

---

## 🛠 Key Features  

1. **Video Search and Save**  
   - Search for YouTube videos using the YouTube Data API and save them for learning purposes.  
   - Manage metadata and user-specific information for saved videos.
   - <img width="487" alt="스크린샷 2024-12-02 오후 2 40 56" src="https://github.com/user-attachments/assets/7d5993a0-3ce2-4e9c-9e75-a7d90233f277">
   - <img width="484" alt="스크린샷 2024-12-02 오후 2 41 11" src="https://github.com/user-attachments/assets/05509e15-9de7-40ca-9a30-654d9e2a971b">

2. **Language-Based Data Extraction**  
   - Analyze Korean (KR) and English (EN) subtitles.  
   - Use the Wikifier API to extract key terms and phrases.  

3. **Bloom's Taxonomy Analysis**  
   - Automatically classify video subtitles into six Bloom's Taxonomy stages (Remember, Understand, Apply, Analyze, Evaluate, Create).  
   - Visualize results with graphs (donut chart and scatter plot)
   - <img width="485" alt="스크린샷 2024-12-02 오후 2 41 29" src="https://github.com/user-attachments/assets/f072efbb-d003-44e1-8f99-5ee7648642fd">
   - <img width="483" alt="스크린샷 2024-12-02 오후 2 42 05" src="https://github.com/user-attachments/assets/7bd87331-5f68-4580-b8ca-04cebc7ff430">

4. **User Data Management**  
   - Efficiently manage user-specific learning data using MongoDB.  
   - Track the learning status of each video (e.g., "learned" or "in progress").  

---

## 🔧 Project Setup  

### 1. Requirements  

- **Python 3.9 or higher**  
- **Django 4.0 or higher**  
- **MongoDB (Atlas)**  

### 2. Installation  

```bash
# 1. Clone the repository
git clone https://github.com/username/BloomScope.git
cd BloomScope

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply migrations
cd Bloom_hub
python manage.py migrate

# 4. Run the local server
python manage.py runserver
```


### 3. API Key Setup  
- Add the GPT api key to the file 'views.py ':
```views.py
def gpt_bloom_classification(self, grouped_sentences):
client = OpenAI (api_key="your-api-key") #Enter the key value here
max_retries = 3 # Maximum retries

valid_stages = {'Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create'}
```
- Please sign up for membership and fill out a valid wikifier_key value before using video analysis.
---

## 📂 Directory Structure  

```plaintext

Bloom_hub/
├── Bloom_hub/                # Main Django project settings and configurations
│   ├── __pycache__/          # Compiled Python files (ignored by Git)
│   ├── __init__.py           # Marks this directory as a Python package
│   ├── asgi.py               # ASGI configuration for asynchronous support
│   ├── settings.py           # Django project settings
│   ├── urls.py               # Project-wide URL configurations
│   ├── wsgi.py               # WSGI configuration for deployment
│   └── ...
├── BloomHub/                 # Core app for your Django project
│   ├── migrations/           # Database migration files
│   ├── static/               # Static files (CSS, JavaScript, images)
│   ├── templates/            # HTML templates
│   ├── __pycache__/          # Compiled Python files (ignored by Git)
│   ├── __init__.py           # Marks this directory as a Python package
│   ├── admin.py              # Django admin site configurations
│   ├── apps.py               # App configuration file
│   ├── models.py             # Database models
│   ├── reserch.py            # Research-related scripts or utilities
│   ├── tests.py              # Unit tests for this app
│   ├── urls.py               # App-specific URL configurations
│   ├── views.py              # Views to handle HTTP requests
│   └── ...
├── venv/                     # Python virtual environment (excluded from Git)
├── manage.py                 # Django management script
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignore rules

```

---

## 📊 Analysis Results  

BloomScope provides two types of graphs based on the analyzed data:  

1. **Donut Chart**: Visualizes the proportion of each Bloom stage.  
2. **Scatter Plot**: Shows the relationship between Bloom stages and time segments.  

---

## 🤝 Contribution  

1. Fork this repository.  
2. Add new features or fix bugs.  
3. Commit your changes:  
   ```bash
   git commit -m "Add a description of your changes"
   ```
4. Submit a pull request.  

---

## 📞 Contact  

For any inquiries related to the project, feel free to reach out via email:  
📧 **marchsnowrabit@gmail.com**  

---

## 🌟 License  

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---


# BloomScope 🌱  
**유튜브 영상에 인지 단계 자동 태깅**  

<img width="1276" alt="image (1)" src="https://github.com/user-attachments/assets/11ba1264-1092-4539-a3b1-115bdafb33a1">

BloomScope는 YouTube 동영상의 자막 데이터를 분석하여 Bloom's Taxonomy의 인지 단계에 따라 자동으로 태깅하고, 학습 목적에 최적화된 정보를 제공합니다. 이 프로젝트는 Django와 MongoDB를 기반으로 구현되었으며, NLP 기술과 GPT 모델을 활용합니다.


[![Velog's GitHub stats](https://velog-readme-stats.vercel.app/api?name=marchsnowrabbit)](https://velog.io/@marchsnowrabbit)



---

## 🛠 주요 기능  

1. **동영상 검색 및 저장**
   - YouTube API를 사용하여 동영상을 검색하고 학습용으로 저장할 수 있습니다.
   - 저장된 동영상의 메타데이터와 사용자 정보를 관리합니다.
   - <img width="484" alt="스크린샷 2024-12-02 오후 2 41 11" src="https://github.com/user-attachments/assets/7d5993a0-3ce2-4e9c-9e75-a7d90233f277">
   - <img width="487" alt="스크린샷 2024-12-02 오후 2 40 56" src="https://github.com/user-attachments/assets/05509e15-9de7-40ca-9a30-654d9e2a971b">
   

2. **언어 기반 데이터 추출**
   - 한국어(KR)와 영어(EN) 자막 데이터를 분석합니다.
   - Wikifier API를 활용하여 중요한 단어와 구문을 추출합니다.

3. **Bloom's Taxonomy 분석**
   - 자막 데이터를 기반으로 Bloom's Taxonomy의 6단계(기억, 이해, 적용, 분석, 평가, 창조)로 자동 분류합니다.
   - 결과는 시각화 그래프로 제공됩니다 (도넛 차트 및 도트 그래프).
   - <img width="485" alt="스크린샷 2024-12-02 오후 2 41 29" src="https://github.com/user-attachments/assets/f072efbb-d003-44e1-8f99-5ee7648642fd">
   - <img width="483" alt="스크린샷 2024-12-02 오후 2 42 05" src="https://github.com/user-attachments/assets/7bd87331-5f68-4580-b8ca-04cebc7ff430">

4. **사용자 데이터 관리**
   - MongoDB를 통해 사용자별 학습 데이터를 효율적으로 관리합니다.
   - 동영상 별로 학습 상태(learned status)를 추적합니다.

---

## 🔧 프로젝트 설정  

### 1. 요구 사항  

- **Python 3.9 이상**
- **Django 4.0 이상**
- **MongoDB (Atlas)**

### 2. 설치 방법  

```bash
# 1. 프로젝트 클론
git clone https://github.com/marchsnowrabbit/BloomScope.git
cd BloomScope

# 2. 패키지 설치
pip install -r requirements.txt

# 3. Django 마이그레이션
cd Bloom_hub
python manage.py migrate

# 4. 로컬 서버 실행
python manage.py runserver

```

### 3. API 키 설정  
- GPT api키를 `views.py` 파일에 추가하세요:
  ```views.py
   def gpt_bloom_classification(self, grouped_sentences):
        client = OpenAI(api_key="your-api-key")  #키값을 여기에 입력
        max_retries = 3  # 최대 재시도 횟수
  
        valid_stages = {'Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create'}

  ```
- 영상 분석을 사용하기 전 회원가입하시고, 유효한 wikifier_key값을 작성해 주세요.
  
---

## 📂 주요 디렉토리 구조  

```plaintext
Bloom_hub/
├── Bloom_hub/                # Django 프로젝트 설정 및 구성
│   ├── __pycache__/          # 컴파일된 Python 파일 (Git에서 제외됨)
│   ├── __init__.py           # 해당 디렉토리를 Python 패키지로 인식
│   ├── asgi.py               # 비동기 지원을 위한 ASGI 설정
│   ├── settings.py           # Django 프로젝트 설정 파일
│   ├── urls.py               # 프로젝트 전반의 URL 설정
│   ├── wsgi.py               # 배포를 위한 WSGI 설정
│   └── ...
├── BloomHub/                 # Django 프로젝트의 핵심 앱 디렉토리
│   ├── migrations/           # 데이터베이스 마이그레이션 파일
│   ├── static/               # 정적 파일 (CSS, JavaScript, 이미지 등)
│   ├── templates/            # HTML 템플릿
│   ├── __pycache__/          # 컴파일된 Python 파일 (Git에서 제외됨)
│   ├── __init__.py           # 해당 디렉토리를 Python 패키지로 인식
│   ├── admin.py              # Django 관리자 설정
│   ├── apps.py               # 앱 구성 파일
│   ├── models.py             # 데이터베이스 모델 정의
│   ├── reserch.py            # 리서치 관련 스크립트나 유틸리티
│   ├── tests.py              # 앱 테스트 코드
│   ├── urls.py               # 앱 전용 URL 설정
│   ├── views.py              # HTTP 요청 처리를 위한 뷰
│   └── ...
├── venv/                     # Python 가상 환경 디렉토리 (Git에서 제외됨)
├── manage.py                 # Django 관리 스크립트
├── README.md                 # 프로젝트 문서 파일
├── requirements.txt          # Python 의존성 패키지 목록
├── .gitignore                # Git에서 제외할 파일 목록

```

---

## 📊 분석 결과  
BloomScope는 학습 데이터를 기반으로 두 가지 그래프를 제공합니다:

1. **도넛 차트**: 각 Bloom 단계의 비율 시각화  
2. **도트 그래프**: Bloom 단계와 시간 구간 간의 관계를 나타냄  

---

## 🤝 기여 방법  

1. 이 저장소를 포크합니다.
2. 새로운 기능을 추가하거나 버그를 수정합니다.
3. 변경 사항을 커밋합니다:
   ```bash
   git commit -m "Add 새로운 기능 설명"
   ```
4. 풀 리퀘스트를 제출합니다.

---

## 📞 문의  

프로젝트 관련 문의 사항은 다음 이메일로 연락해주세요:  
📧 **marchsnowrabbit@gmail.com**

---

## 🌟 라이선스  

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참고하세요.

--- 
