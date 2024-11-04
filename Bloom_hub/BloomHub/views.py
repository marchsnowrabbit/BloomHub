import os,json, logging,string
import isodate,urllib,csv,re
import random
import pandas as pd
import urllib.parse,urllib.request
import nltk, spacy
import concurrent.futures
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from nltk.corpus import stopwords
from django.contrib import messages
from googleapiclient.discovery import build
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.conf import settings
from pymongo import MongoClient
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import CouldNotRetrieveTranscript
from konlpy.tag import Okt
from .models import WordData, SentenceData  # 모델 임포트

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class YoutubeVideoapi:
    def __init__(self):
        self.developer_key = os.getenv('YOUTUBE_API_KEY', 'AIzaSyA7Qn-gNPnDQ4xgpDemtU0OzArCzL0zqvI')
        self.youtube_api_service_name = "youtube"
        self.youtube_api_version = 'v3'

    def videolist(self, keyword, page_token=None):
        youtube = build(self.youtube_api_service_name, self.youtube_api_version, developerKey=self.developer_key)

        try:
            search_response = youtube.search().list(
                q=keyword,
                order='viewCount',
                part='snippet',
                maxResults=50,
                pageToken=page_token
            ).execute()

            video_ids = []
            videos = []
            for item in search_response['items']:
                video_id = item['id'].get('videoId')
                if video_id:
                    video_ids.append(video_id)

            if video_ids:
                videos_response = youtube.videos().list(
                    id=','.join(video_ids),
                    part='snippet,contentDetails,statistics'
                ).execute()

                for video in videos_response['items']:
                    duration = video['contentDetails']['duration']
                    duration_obj = isodate.parse_duration(duration)

                    # 90초 이하인 동영상 필터링
                    if duration_obj.total_seconds() <= 90:
                        continue

                    videos.append({
                        'title': video['snippet']['title'],
                        'videoId': video['id'],
                        'thumbnail': video['snippet']['thumbnails']['default']['url'],
                        'channelTitle': video['snippet']['channelTitle'],
                        'duration': self.convert_duration(duration),
                        'viewCount': video['statistics'].get('viewCount', 0),
                    })

            next_page_token = search_response.get('nextPageToken')
            prev_page_token = search_response.get('prevPageToken')

            return videos, next_page_token, prev_page_token

        except Exception as e:
            logger.error(f"오류 발생: {e}")
            return [], None, None

    def get_video_details(self, video_id):
        youtube = build(self.youtube_api_service_name, self.youtube_api_version, developerKey=self.developer_key)
        
        try:
            video_response = youtube.videos().list(
                id=video_id,
                part='snippet,statistics,contentDetails'
            ).execute()

            if video_response['items']:
                video = video_response['items'][0]
                has_caption = video['contentDetails'].get('caption') == 'true'  # 자막 유무 확인

                 # duration을 두 가지 형식으로 가져옵니다.
                duration = video['contentDetails']['duration']
                duration_seconds = int(isodate.parse_duration(duration).total_seconds())  # 초 단위

                return {
                    'title': video['snippet']['title'],
                    'thumbnail': video['snippet']['thumbnails']['default']['url'],
                    'viewCount': video['statistics'].get('viewCount', 0),
                    'channelTitle': video['snippet']['channelTitle'],
                    'duration': self.convert_duration(duration),  # 사람이 읽기 쉬운 형식
                    'duration_seconds': duration_seconds,  # 초 단위로 저장용
                    'videoId': video_id,
                    'hasCaption': has_caption
                }
        except Exception as e:
            logger.error(f"비디오 세부 정보 조회 오류: {e}")
        
        return None

    def convert_duration(self, duration):
        duration_obj = isodate.parse_duration(duration)
        total_minutes = int(duration_obj.total_seconds() // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}시간 {minutes}분" if hours > 0 else f"{minutes}분"

def search(request):
    keyword = request.POST.get('keyword') or request.GET.get('keyword', '')
    page_token = request.GET.get('pageToken')  # 페이지 토큰 추가

    videos, next_page_token, prev_page_token = [], None, None
    if keyword:  # 검색어가 있을 때만 API 호출
        video_api = YoutubeVideoapi()
        videos, next_page_token, prev_page_token = video_api.videolist(keyword, page_token)

    if not keyword:
        return render(request, 'search.html')
    
        if not videos:
            messages.error(request, '비디오를 찾을 수 없습니다.')

    return render(request, 'searchresult.html', {
        'videos': videos,
        'keyword': keyword,
        'next_page_token': next_page_token,
        'prev_page_token': prev_page_token
    })



def study(request, video_id):
    video_api = YoutubeVideoapi()
    video_info = video_api.get_video_details(video_id)

    if video_info is None:
        return render(request, 'study.html', {'error': '비디오 정보를 불러올 수 없습니다.'})

    video_info['videoId'] = video_id
    return render(request, 'study.html', {'video': video_info})

###########영상저장하기################################
# 학습할 영상 저장
@login_required
@csrf_exempt
def save_learning_video(request):
    if request.method == "POST":
        data = json.loads(request.body)
        video_id = data.get("vid")
        user_id = request.user.user_id  # 현재 로그인한 사용자의 user_id 가져오기
        
        learning_video, created = LearningVideo.objects.update_or_create(
            vid=video_id,
            defaults={
                'title': data.get("title"),
                'setTime': data.get("setTime"),
                'uploader': data.get("uploader"),
                'view_count': data.get("view_count"),
                'std_lang': data.get("std_lang"),
                'user_id': user_id,
                'learning_status': False
            }
        )
        
        return JsonResponse({"success": True, "created": created})
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=400)


# vid가 YouTube 링크인지 검증하는 함수
def is_valid_youtube_url(video_id):
    return bool(re.match(r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$', video_id))

#추출기
class KoreanScriptExtractor:
    def __init__(self, vid, setTime, wikiUserKey, NUM_OF_WORDS=5):
        self.vid = vid if is_valid_youtube_url(vid) else f"https://www.youtube.com/watch?v={vid}"
        self.setTime = setTime
        self.wikiUserKey = wikiUserKey
        self.NUM_OF_WORDS = NUM_OF_WORDS
        self.segments = []
        self.sentences_for_gpt = []  # GPT 분석용 문장 저장
        self.stopwords = self.load_stopwords_from_mongo()
        self.okt = Okt()
        self.video_title = self.get_video_title()

    def load_stopwords_from_mongo(self):
        client = MongoClient(settings.MONGO_URI)
        db = client["BloomHub"]
        collection = db["bloom_dictionary"]
        
        # MongoDB에서 'stopwords-ko' 데이터를 가져오기
        stopwords_data = collection.find_one({"language": "Korean", "stage": "stopwords-ko"})
        return stopwords_data['words'] if stopwords_data else []

    def get_video_title(self):
        video_id = self.vid.split("v=")[1]
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        title = re.search(r'<title>(.*?)</title>', html).group(1)
        return title.replace(' - YouTube', '').strip()

    def extract(self):
        video_id = self.vid.split("v=")[1]

        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            self.scriptData = None
            for transcript in transcript_list:
                if transcript.language_code == 'ko':
                    self.scriptData = transcript.fetch()
                    break

            # 자막이 없을 경우 경고 메시지를 표시하고 종료
            if not self.scriptData:
                print("This video doesn't have Korean captions.")
                return

        except CouldNotRetrieveTranscript:
            print("Captions are disabled or unavailable for this video.")
            return
        
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return


        segment_duration = 60
        start_time = 0
        end_time = segment_duration
        segment_texts = []

        for segment in self.scriptData:
            if start_time <= segment['start'] < end_time:
                segment_texts.append(segment['text'])
            elif segment['start'] >= end_time:
                self.add_segment(segment_texts, start_time, end_time)
                segment_texts = [segment['text']]
                start_time = end_time
                end_time += segment_duration

        if segment_texts:
            self.add_segment(segment_texts, start_time, end_time)

    def add_segment(self, texts, start_time, end_time):
        segment_data = {
            "text": " ".join(texts),
            "start_time": start_time,
            "end_time": end_time
        }
        self.segments.append(segment_data)

        # gpt 분석을 위한 문장별로 저장
        for text in texts:
            self.sentences_for_gpt.append({
                "word": text,
                "start_time": start_time,
                "end_time": end_time
            })

    def konlpy_analysis(self):
        for segment in self.segments:
            analyzed_segment = self.okt.pos(segment['text'], stem=True)
            nouns = [word for word, pos in analyzed_segment if pos.startswith('N')]
            verbs = [word for word, pos in analyzed_segment if pos.startswith('V')]
            filtered_nouns = [word for word in nouns if word not in self.stopwords]
            filtered_verbs = [word for word in verbs if word not in self.stopwords]
            segment['nouns'] = filtered_nouns
            segment['verbs'] = filtered_verbs

    def url_to_wiki(self):
        self.extract()
        self.konlpy_analysis()
        if not self.scriptData:
            return pd.DataFrame()

        results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_segment = {executor.submit(self.call_wikifier, segment['text']): segment for segment in self.segments}
            for future in concurrent.futures.as_completed(future_to_segment):
                segment = future_to_segment[future]
                try:
                    wikifier_result = future.result()
                    for res in wikifier_result:
                        res['segment'] = segment
                    results.extend(wikifier_result)
                except Exception as e:
                    print(f"Error during Wikifier API call: {e}")

        wiki_data = []
        for result in results:
            segment = result.pop('segment')
            for noun in segment['nouns']:
                result_copy = result.copy()
                result_copy['word'] = noun
                result_copy['pos'] = 'noun'
                result_copy['start_time'] = segment['start_time']
                result_copy['end_time'] = segment['end_time']
                result_copy['title'] = self.video_title
                wiki_data.append(result_copy)
            for verb in segment['verbs']:
                result_copy = result.copy()
                result_copy['word'] = verb
                result_copy['pos'] = 'verb'
                result_copy['start_time'] = segment['start_time']
                result_copy['end_time'] = segment['end_time']
                result_copy['title'] = self.video_title
                wiki_data.append(result_copy)

        df = pd.DataFrame(wiki_data)
        df.drop(columns=['segment_text'], inplace=True, errors='ignore')
        return df

    def call_wikifier(self, text, lang="ko", threshold=0.8, numberOfKCs=10):
        data = urllib.parse.urlencode({
            "text": text,
            "lang": lang,
            "userKey": self.wikiUserKey,
            "pageRankSqThreshold": "%g" % threshold,
            "applyPageRankSqThreshold": "true",
            "nTopDfValuesToIgnore": "200",
            "nWordsToIgnoreFromList": "200",
            "wikiDataClasses": "false",
            "wikiDataClassIds": "false",
            "support": "false",
            "ranges": "false",
            "minLinkFrequency": "3",
            "includeCosines": "false",
            "maxMentionEntropy": "2"
        }).encode('utf-8')

        url = "https://www.wikifier.org/annotate-article"
        req = urllib.request.Request(url, data=data, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as f:
                response = json.loads(f.read().decode('utf-8'))
        except Exception as e:
            print(f"Error calling Wikifier API: {e}")
            return []

        sorted_data = sorted(response.get('annotations', []), key=lambda x: x['pageRank'], reverse=True)
        return [{"title": ann["title"], "url": ann["url"], "pageRank": ann["pageRank"]} for ann in sorted_data[:numberOfKCs]]

    def save_sentences_for_gpt(self):
        with open('sentences_for_gpt.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["title", "word", "start_time", "end_time"])
    
            time_segments = {}
            for sentence in self.sentences_for_gpt:
                time_key = (sentence['start_time'], sentence['end_time'])
                if time_key not in time_segments:
                    time_segments[time_key] = []
            
                cleaned_text = sentence['word'].replace('\n', ' ').replace('\r', ' ')
                time_segments[time_key].append(cleaned_text)
    
            for (start_time, end_time), texts in time_segments.items():
                combined_text = "".join(texts)
                writer.writerow([self.video_title, combined_text, start_time, end_time])

# nltk 불용어 다운로드 (최초 실행 시 한 번 필요)
nltk.download('stopwords')

# 영어 추출기
class EnglishScriptExtractor:
    def __init__(self, vid, setTime, wikiUserKey, NUM_OF_WORDS=5):
        self.vid = vid if is_valid_youtube_url(vid) else f"https://www.youtube.com/watch?v={vid}"
        self.setTime = setTime
        self.wikiUserKey = wikiUserKey
        self.NUM_OF_WORDS = NUM_OF_WORDS
        self.segments = []
        self.sentences_for_gpt = []  # GPT 분석용 문장 저장
        self.nlp = spacy.load('en_core_web_sm')
        self.stop_words = set(stopwords.words('english'))
        self.video_title = self.get_video_title()

    def get_video_title(self):
        video_id = self.vid.split("v=")[1]
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        title = re.search(r'<title>(.*?)</title>', html).group(1)
        return title.replace(' - YouTube', '').strip()

    def extract(self):
        video_id = self.vid.split("v=")[1]

        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            self.scriptData = None
            for transcript in transcript_list:
                if transcript.language_code == 'en':
                    self.scriptData = transcript.fetch()
                    break

            # 자막이 없을 경우 경고 메시지를 표시하고 종료
            if not self.scriptData:
                print("This video doesn't have English captions.")
                return

        except CouldNotRetrieveTranscript:
            print("Captions are disabled or unavailable for this video.")
            return
        
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return

        segment_duration = 60
        start_time = 0
        end_time = segment_duration
        segment_texts = []

        for segment in self.scriptData:
            if start_time <= segment['start'] < end_time:
                segment_texts.append(segment['text'])
            elif segment['start'] >= end_time:
                self.add_segment(segment_texts, start_time, end_time)
                segment_texts = [segment['text']]
                start_time = end_time
                end_time += segment_duration

        if segment_texts:
            self.add_segment(segment_texts, start_time, end_time)

    def add_segment(self, texts, start_time, end_time):
        segment_data = {
            "text": " ".join(texts),
            "start_time": start_time,
            "end_time": end_time
        }
        self.segments.append(segment_data)

        # GPT 분석용 문장 저장
        for text in texts:
            self.sentences_for_gpt.append({
                "word": text,
                "start_time": start_time,
                "end_time": end_time
            })

    def spacy_analysis(self):
        for segment in self.segments:
            doc = self.nlp(segment['text'])
            nouns = [token.text for token in doc if token.pos_ == 'NOUN' and token.text.lower() not in self.stop_words]
            verbs = [token.lemma_ for token in doc if token.pos_ == 'VERB' and token.lemma_.lower() not in self.stop_words]
            segment['nouns'] = nouns
            segment['verbs'] = verbs

    def url_to_wiki(self):
        self.extract()
        self.spacy_analysis()
        if not self.scriptData:
            return pd.DataFrame()

        results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_segment = {executor.submit(self.call_wikifier, segment['text']): segment for segment in self.segments}
            for future in concurrent.futures.as_completed(future_to_segment):
                segment = future_to_segment[future]
                try:
                    wikifier_result = future.result()
                    for res in wikifier_result:
                        res['segment'] = segment
                    results.extend(wikifier_result)
                except Exception as e:
                    print(f"Error during Wikifier API call: {e}")

        wiki_data = []
        for result in results:
            segment = result.pop('segment')
            for noun in segment['nouns']:
                result_copy = result.copy()
                result_copy['word'] = noun
                result_copy['pos'] = 'noun'
                result_copy['start_time'] = segment['start_time']
                result_copy['end_time'] = segment['end_time']
                result_copy['title'] = self.video_title
                wiki_data.append(result_copy)
            for verb in segment['verbs']:
                result_copy = result.copy()
                result_copy['word'] = verb
                result_copy['pos'] = 'verb'
                result_copy['start_time'] = segment['start_time']
                result_copy['end_time'] = segment['end_time']
                result_copy['title'] = self.video_title
                wiki_data.append(result_copy)

        df = pd.DataFrame(wiki_data)
        df.drop(columns=['segment_text'], inplace=True, errors='ignore')
        return df

    def call_wikifier(self, text, lang="en", threshold=0.8, numberOfKCs=10):
        data = urllib.parse.urlencode({
            "text": text,
            "lang": lang,
            "userKey": self.wikiUserKey,
            "pageRankSqThreshold": "%g" % threshold,
            "applyPageRankSqThreshold": "true",
            "nTopDfValuesToIgnore": "200",
            "nWordsToIgnoreFromList": "200",
            "wikiDataClasses": "false",
            "wikiDataClassIds": "false",
            "support": "false",
            "ranges": "false",
            "minLinkFrequency": "3",
            "includeCosines": "false",
            "maxMentionEntropy": "2"
        }).encode('utf-8')

        url = "https://www.wikifier.org/annotate-article"
        req = urllib.request.Request(url, data=data, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as f:
                response = json.loads(f.read().decode('utf-8'))
        except Exception as e:
            print(f"Error calling Wikifier API: {e}")
            return []

        sorted_data = sorted(response.get('annotations', []), key=lambda x: x['pageRank'], reverse=True)
        return [{"title": ann["title"], "url": ann["url"], "pageRank": ann["pageRank"]} for ann in sorted_data[:numberOfKCs]]

    def save_sentences_for_gpt(self):
        # GPT 분석용 문장을 시간대별로 결합하여 시작 시간과 종료 시간을 포함해 저장, 문장에 줄바꿈 문자도 추가
        with open('sentences_for_gpt.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["title", "word", "start_time", "end_time"])
    
            # 시간대별로 문장 결합
            time_segments = {}
            for sentence in self.sentences_for_gpt:
                time_key = (sentence['start_time'], sentence['end_time'])
                if time_key not in time_segments:
                    time_segments[time_key] = []
            
                # 줄바꿈 문자 제거 후 저장
                cleaned_text = sentence['word'].replace('\n', ' ').replace('\r', ' ')
                time_segments[time_key].append(cleaned_text)
    
            # 각 시간대별 문장들을 줄바꿈으로 결합하여 저장
            for (start_time, end_time), texts in time_segments.items():
                combined_text = "".join(texts)
                writer.writerow([self.video_title, combined_text, start_time, end_time])

def get_mongo_connection():
    # settings.py의 DATABASES 설정에서 MongoDB 연결 정보 가져오기
    client = MongoClient(settings.DATABASES['default']['CLIENT']['host'])
    db = client[settings.DATABASES['default']['NAME']]
    return db

# 추출 결과를 MongoDB에 저장하는 함수
def run_extractor_and_save_to_db(request):
    if request.method == "POST":
        data = json.loads(request.body)
        video_id = data.get("video_id")
        set_time = data.get("setTime")
        std_lang = data.get("std_lang")
        wikifier_api_key = request.user.wikifier_api_key
        user_id = request.user.user_id

        if not video_id or not set_time:
            return JsonResponse({"success": False, "error": "video_id and setTime are required."})

        # vid가 링크 형태가 아니면 링크로 변환
        if not is_valid_youtube_url(video_id):
            video_id = f"https://www.youtube.com/watch?v={video_id}"

        video, created = LearningVideo.objects.update_or_create(
            vid=video_id,
            defaults={
                'title': data.get("title"),
                'setTime': data.get("setTime"),
                'uploader': data.get("uploader"),
                'view_count': data.get("view_count"),
                'std_lang': data.get("std_lang"),
                'user_id': user_id,
                'learning_status': False
            }
        )

        # 언어에 따라 적절한 추출기를 선택
        if std_lang == "KR":
            extractor = KoreanScriptExtractor(vid=video_id, setTime=set_time, wikiUserKey=wikifier_api_key)
        elif std_lang == "EN":
            extractor = EnglishScriptExtractor(vid=video_id, setTime=set_time, wikiUserKey=wikifier_api_key)
        else:
            return JsonResponse({"success": False, "error": "Invalid language selection."})

        # 데이터 추출
        word_data_df = extractor.url_to_wiki()
        sentence_data = extractor.sentences_for_gpt

        # WordData 저장
        word_data_objects = [
            WordData(
                video = video,
                url=row['url'],
                page_rank=row['pageRank'],
                word=row['word'],
                pos=row['pos'],
                start_time=row['start_time'],
                end_time=row['end_time']
            ) for index, row in word_data_df.iterrows()
        ]
        WordData.objects.bulk_create(word_data_objects)

        # SentenceData 저장 (동일 구간의 문장을 하나로 합침)
        sentence_data_combined = {}
        for sentence in sentence_data:
            time_key = (sentence["start_time"], sentence["end_time"])
            if time_key not in sentence_data_combined:
                sentence_data_combined[time_key] = []
            sentence_data_combined[time_key].append(sentence["word"])
        
        sentence_data_objects = [
                SentenceData(
                    video=video,
                    word=" ".join(words),  # 같은 구간의 문장들을 하나로 결합
                    start_time=start_time,
                    end_time=end_time
                )
                for (start_time, end_time), words in sentence_data_combined.items()
            ]

        SentenceData.objects.bulk_create(sentence_data_objects)

        return JsonResponse({"success": True, "message": "Data saved successfully."})

    return JsonResponse({"success": False, "error": "Invalid request method."}, status=400)

#############################################회원용#################
# 중복 체크 API 뷰
def check_duplicate(request):
    field = request.GET.get('field')
    value = request.GET.get('value')
    
    logger.info(f"Received check_duplicate request with field: {field}, value: {value}")

    if not field or not value:
        logger.error("필드 또는 값이 전달되지 않았습니다.")
        return JsonResponse({'error': '필드 또는 값이 전달되지 않았습니다.'}, status=400)

    if field == 'user_id':
        exists = bool(BloomUser.objects.filter(user_id=value).values('user_id').first())
    elif field == 'email':
        exists = bool(BloomUser.objects.filter(email=value).values('email').first())
    else:
        logger.error("잘못된 필드가 요청되었습니다.")
        return JsonResponse({'error': '잘못된 필드입니다.'}, status=400)

    return JsonResponse({'exists': exists})

# 회원가입 뷰
def signup_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        username = request.POST.get('username')
        password = request.POST.get('password1')
        password_confirm = request.POST.get('password2')
        email = request.POST.get('email')
        youtube_api_key = request.POST.get('youtube_api_key')
        wikifier_api_key = request.POST.get('wikifier_api_key')

        logger.info(f"Signup attempt: user_id={user_id}, email={email}")

        if password != password_confirm:
            messages.error(request, "비밀번호가 일치하지 않습니다.")
            return render(request, 'signup.html')

        hashed_password = make_password(password)

        try:
            user = BloomUser.objects.create(
                user_id=user_id,
                username=username,
                email=email,
                password=hashed_password,
                youtube_api_key=youtube_api_key,
                wikifier_api_key=wikifier_api_key,
            )
            messages.success(request, "회원가입이 완료되었습니다.")
            logger.info("User created successfully.")
            return redirect('login')
        except Exception as e:
            logger.error(f"오류가 발생했습니다: {e}")
            messages.error(request, f"오류가 발생했습니다: {str(e)}")

    return render(request, 'signup.html')

# 로그인 뷰
def login_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        password = request.POST.get('password')

        try:
            user = BloomUser.objects.get(user_id=user_id)
        except BloomUser.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'user_id'})

        if user.check_password(password):
            login(request, user)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'password'})

    return render(request, 'login.html')

# 로그인 상태 확인 API 뷰
def check_login(request):
    is_logged_in = request.user.is_authenticated
    username = request.user.username if is_logged_in else ""
    return JsonResponse({'is_logged_in': is_logged_in, 'username': username})

# 로그아웃 뷰
def logout_view(request):
    logout(request)
    return redirect('home')

# 이메일 인증번호 생성 함수
def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

# 인증번호 발송 뷰
def send_verification_code(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = BloomUser.objects.get(email=email)
            verification_code = generate_verification_code()
            request.session['verification_code'] = verification_code
            request.session['verification_expiry'] = (timezone.now() + timedelta(minutes=10)).timestamp()

            # 이메일 발송
            send_mail(
                'Your Verification Code',
                f'Your verification code is {verification_code}.',
                'noreply@example.com',
                [email],
                fail_silently=False,
            )
            return JsonResponse({'success': True, 'message': '인증번호가 발송되었습니다.'})
        except BloomUser.DoesNotExist:
            return JsonResponse({'success': False, 'message': '등록된 이메일이 아닙니다.'})
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

# 인증번호 확인 뷰
def verify_code_and_find_id(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        code = request.POST.get('verification_code')

        stored_code = request.session.get('verification_code')
        expiry = request.session.get('verification_expiry')
        
        if timezone.now().timestamp() > expiry:
            return JsonResponse({'success': False, 'message': '인증번호가 만료되었습니다.'})
        
        if code == stored_code:
            user = BloomUser.objects.get(email=email)
            return JsonResponse({'success': True, 'found_id': user.user_id})
        else:
            return JsonResponse({'success': False, 'message': '인증번호가 일치하지 않습니다.'})
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

#######################비밀번호 찾기용 #####################################################ㄸ#
# 비밀번호 찾기용 인증번호 발송 뷰
def send_verification_code_for_password_reset(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        email = request.POST.get('email')

        # ID와 이메일이 모두 일치하는 사용자를 조회
        try:
            user = BloomUser.objects.get(user_id=user_id, email=email)
            verification_code = generate_verification_code()
            request.session['password_reset_verification_code'] = verification_code
            request.session['verification_expiry'] = (timezone.now() + timedelta(minutes=10)).timestamp()

            # 이메일 발송
            send_mail(
                'Password Reset Verification Code',
                f'Your password reset verification code is {verification_code}.',
                'noreply@example.com',
                [email],
                fail_silently=False,
            )
            return JsonResponse({'success': True, 'message': '인증번호가 발송되었습니다.'})
        except BloomUser.DoesNotExist:
            # ID 또는 이메일이 잘못된 경우 오류 메시지 반환
            return JsonResponse({'success': False, 'message': '입력한 ID와 이메일이 일치하지 않습니다.'})
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

# 인증번호 확인 뷰 (비밀번호 찾기)
def verify_code_for_password_reset(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        email = request.POST.get('email')
        code = request.POST.get('verification_code')
        stored_code = request.session.get('password_reset_verification_code')
        expiry = request.session.get('verification_expiry')
        
        if timezone.now().timestamp() > expiry:
            return JsonResponse({'success': False, 'message': '인증번호가 만료되었습니다.'})
        
        if code == stored_code:
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'message': '인증번호가 일치하지 않습니다.'})
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

# 비밀번호 재설정 뷰
def reset_password(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            return JsonResponse({'success': False, 'message': '비밀번호가 일치하지 않습니다.'})

        try:
            user = BloomUser.objects.get(user_id=user_id)
            user.set_password(new_password)
            user.save()
            return JsonResponse({'success': True, 'message': '비밀번호가 업데이트되었습니다.'})
        except BloomUser.DoesNotExist:
            return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})


###########################################################################################
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render
from .models import BloomUser, LearningVideo  # 사용자 모델 임포트

# 이메일 변경 뷰
@login_required
def change_email(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_email = request.POST.get('new_email')

        user = request.user  # 현재 로그인한 사용자

        # 비밀번호 확인
        if not user.check_password(current_password):
            return JsonResponse({'success': False, 'message': '비밀번호가 일치하지 않습니다.'})

        # 이메일 중복 체크
        if BloomUser.objects.filter(email=new_email).exists():
            return JsonResponse({'success': False, 'message': '이미 사용 중인 이메일입니다.'})

        # 이메일 업데이트
        try:
            user.email = new_email
            user.save()
            return JsonResponse({'success': True, 'message': '이메일이 성공적으로 변경되었습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

###########################################################################################
# 페이지 렌더링 뷰들
def home(request):
    return render(request, 'home.html')

def home_kor(request):
    return render(request, 'homekor.html')

def guide(request):
    return render(request, 'guide.html')

def guide_kor(request):
    return render(request, 'guidekor.html')

def learning(request):
    return render(request, 'learning.html')

def learning_kor(request):
    return render(request, 'learningkor.html')

def learned(request):
    return render(request, 'learned.html')

def learned_kor(request):
    return render(request, 'learnedkor.html')

def login_page(request):
    return render(request, 'login.html')

def login_kor(request):
    return render(request, 'loginkor.html')

def signup_page(request):
    return render(request, 'signup.html')

def signup_kor(request):
    return render(request, 'signupkor.html')

def mypage(request):
    return render(request, 'mypage.html')

def mypage_kor(request):
    return render(request, 'mypagekor.html')

def mypage_manager(request):
    return render(request, 'mypagemanager.html')

def search_kor(request):
    return render(request, 'searchkor.html')

def search_result(request):
    return render(request, 'searchresult.html')

def search_result_kor(request):
    return render(request, 'searchresultkor.html')

def find_id(request):
    return render(request, 'findID.html')

def find_id_kor(request):
    return render(request, 'findIDkor.html')

def find_pwd(request):
    return render(request, 'findpwd.html')

def find_pwd_kor(request):
    return render(request, 'findpwdkor.html')

def analysis(request):
    return render(request, 'analysis.html')
