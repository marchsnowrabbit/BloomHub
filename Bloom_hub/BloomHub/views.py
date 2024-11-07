import os,json,logging,string
import traceback
import isodate,urllib,csv,re,time
import random
import pandas as pd
import urllib.parse,urllib.request
import nltk, spacy
import concurrent.futures
from django.shortcuts import get_object_or_404, render, redirect
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
from .models import WordData, SentenceData, AnalysisResult  # 모델 임포트
from django.apps import apps
from collections import Counter
import plotly.io as pio
import plotly.express as px
import plotly.graph_objects as go
from sklearn.feature_extraction.text import TfidfVectorizer
from openai import OpenAI, max_retries


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

def search_kor(request):
    keyword = request.POST.get('keyword') or request.GET.get('keyword', '')
    page_token = request.GET.get('pageToken')  # 페이지 토큰 추가

    videos, next_page_token, prev_page_token = [], None, None
    if keyword:  # 검색어가 있을 때만 API 호출
        video_api = YoutubeVideoapi()
        videos, next_page_token, prev_page_token = video_api.videolist(keyword, page_token)

    if not keyword:
        return render(request, 'searchkor.html')
    
        if not videos:
            messages.error(request, '비디오를 찾을 수 없습니다.')

    return render(request, 'searchresultkor.html', {
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
        # MongoDB 연결 설정
        client = MongoClient(settings.MONGO_URI)
        db = client["BloomHub"]
        collection = db["bloom_dictionary"]
        
        # MongoDB에서 'stopwords-ko' 데이터를 가져오기
        stopwords_data = collection.find_one({"language": "Korean", "stage": "stopwords-ko"})
        
        # JSON 리스트 형식을 문자열 리스트로 변환
        if stopwords_data:
            return [str(word) for word in stopwords_data.get('words', [])]
        return []

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

# YouTube 링크에서 비디오 ID만 추출하는 함수
def extract_video_id(youtube_url):
    import re
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", youtube_url)
    return match.group(1) if match else youtube_url

logger = logging.getLogger('myapp')

#추출기 실행 및 데이터 저장
def run_extractor_and_save_to_db(request):
    if request.method == "POST":
        data = json.loads(request.body)

        video_url = data.get("video_id")
        set_time = data.get("setTime")
        std_lang = data.get("std_lang")
        wikifier_api_key = request.user.wikifier_api_key
        user_id = request.user.user_id

        video_id = extract_video_id(video_url)
        if not video_id or not set_time:
            return JsonResponse({"success": False, "error": "video_id and setTime are required."})

        # MongoDB 연결
        db = get_mongo_connection()
        learning_video_collection = db['BloomHub_learningvideo']
        worddata_collection = db['BloomHub_worddata']
        sentencedata_collection = db['BloomHub_sentencedata']

        # LearningVideo 저장 또는 업데이트
        learning_video_collection.update_one(
            {"vid": video_id},
            {"$set": {
                'title': data.get("title"),
                'setTime': set_time,
                'uploader': data.get("uploader"),
                'view_count': data.get("view_count"),
                'std_lang': std_lang,
                'user_id': user_id,
                'learning_status': False
            }},
            upsert=True
        )

        # 기존에 저장된 추출 데이터 확인
        existing_word_data = worddata_collection.count_documents({"video_id": video_id}) > 0
        existing_sentence_data = sentencedata_collection.count_documents({"video_id": video_id}) > 0

        # 데이터가 이미 존재할 경우 분석기로 넘어가기
        if existing_word_data and existing_sentence_data:
            return run_analysis(request, video_id)

        # 언어에 따라 적절한 추출기 선택
        if std_lang == "KR":
            extractor = KoreanScriptExtractor(vid=video_url, setTime=set_time, wikiUserKey=wikifier_api_key)
        elif std_lang == "EN":
            extractor = EnglishScriptExtractor(vid=video_url, setTime=set_time, wikiUserKey=wikifier_api_key)
        else:
            return JsonResponse({"success": False, "error": "Invalid language selection."})

        return JsonResponse({"success": True, "message": "Data saved successfully."})

    return JsonResponse({"success": False, "error": "Invalid request method."}, status=400)

#분석기
class BloomAnalysisWithGPTandDictionary:
    def __init__(self, video_id, language):
        self.video_id = video_id
        self.language = language
        self.word_data = self.load_data_from_db("WordData")
        self.sentence_data = self.load_data_from_db("SentenceData")
        self.bloom_dict_ko = self.load_bloom_dictionary_from_db("Korean")
        self.bloom_dict_en = self.load_bloom_dictionary_from_db("English")
        self.bloom_priority = {
            'remember': 6, 'understand': 5, 'apply': 4,
            'analyze': 3, 'evaluate': 2, 'create': 1
        }
        self.gpt_classification_results = {}  # GPT 분석 결과 초기화
        logger.info("BloomAnalysisWithGPTandDictionary initialized.")

    def load_data_from_db(self, model_name):
        Model = apps.get_model('BloomHub', model_name)
        data = Model.objects.filter(video__vid=self.video_id).values()
        logger.info(f"Data loaded from {model_name} for video_id {self.video_id}: {len(data)} records")
        return pd.DataFrame(data)

    @staticmethod
    def load_bloom_dictionary_from_db(language):
        BloomDictionary = apps.get_model('BloomHub', 'BloomDictionary')
        bloom_dict = {}
        stages = ["remember", "understand", "apply", "analyze", "evaluate", "create"]

        for stage in stages:
            entry = BloomDictionary.objects.filter(language=language, stage=stage).first()
            if entry:
                words = json.loads(entry.words) if isinstance(entry.words, str) else entry.words
                bloom_dict[stage] = [word for word in words if word != "word"]
                logger.info(f"Bloom dictionary for {language} - Stage: {stage}, Words count: {len(bloom_dict[stage])}")
        return bloom_dict

    def detect_language(self):
        self.word_data['language'] = self.word_data['word'].str.contains('[\u3131-\uD79D]').map(
            {True: 'Korean', False: 'English'}
        )
        logger.info("Language detection completed. Language data added to word data.")

    def process_verbs(self):
        self.detect_language()
        verbs = self.word_data[self.word_data['pos'] == 'verb'].copy()
        self.verb_counts = verbs.groupby(['start_time', 'end_time', 'word', 'language']).size().reset_index(name='count')
        self.verb_counts['bloom_stage'] = self.verb_counts.apply(
            lambda row: self.determine_final_bloom_stage(row['word'], row['language'], row['start_time'], row['end_time']),
            axis=1
        )
        logger.info(f"Verbs processed successfully. Verb counts:\n{self.verb_counts}")

    def tag_bloom_stage(self, word, language):
        bloom_dict = self.bloom_dict_ko if language == 'Korean' else self.bloom_dict_en
        for stage, words in bloom_dict.items():
            if word in words:
                logger.debug(f"Word '{word}' matched with stage '{stage}' for language '{language}'")
                return stage
        logger.debug(f"Word '{word}' not found in any stage for language '{language}'")
        return 'unknown'
    
    def gpt_bloom_classification(self, grouped_sentences):
        client = OpenAI(api_key="your-api-key")  # API 키는 적절히 관리
        max_retries = 3  # 최대 재시도 횟수

        results = {}  # 결과를 저장할 딕셔너리
        valid_stages = {'Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create'}

        for (start_time, end_time), combined_text in grouped_sentences.items():
            # 각 텍스트 구간에 대해 GPT에 요청할 메시지 준비
            user_content = (
                f"The following text is from {start_time}s to {end_time}s:\n\n"
                f"{combined_text}\n\n"
                "Please break this text into complete sentences. Then, classify each sentence "
                "according to Bloom's Taxonomy as one of the following stages: 'Remember', 'Understand', "
                "'Apply', 'Analyze', 'Evaluate', or 'Create'.\n\n"
                "Format each sentence with its classification like this:\n"
                "- Sentence: <Complete Sentence>\n- Stage: <Bloom's Taxonomy Stage>"
            )

            messages = [
                {"role": "system", "content": "You are a helpful assistant that classifies text into Bloom's Taxonomy stages."},
                {"role": "user", "content": user_content}
            ]

            for attempt in range(max_retries):
                try:
                    # GPT 모델에 요청 전송
                    completion = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        temperature=0.0,
                        timeout=30
                    )

                     # 올바른 형식으로 응답 추출
                    raw_response = completion.choices[0].message.content
                    print("\nGPT Processed Response:\n", raw_response)  # 디버깅용 출력

                    # 응답을 줄 단위로 나누고 빈 줄 제거
                    response_lines = [line.strip() for line in raw_response.split('\n') if line.strip()]

                    # 단계 단어만 추출
                    stage_lines = [
                        line.split(": ")[1] for line in response_lines 
                        if line.startswith("- Stage:") and line.split(": ")[1] in valid_stages
                    ]

                    # 단계 추출 성공 여부 로깅
                    if stage_lines:
                        logger.info(f"Bloom stages for segment {start_time}-{end_time}: {stage_lines}")
                    else:
                        logger.warning(f"No valid Bloom stages found for segment {start_time}-{end_time}. Defaulting to 'unknown'.")

                    # 결과를 저장
                    results[(start_time, end_time)] = stage_lines if stage_lines else ['unknown']
                    print(f"GPT classification for segment {start_time}-{end_time} completed successfully.")
                    break  # 성공적으로 처리된 경우 루프 종료

                except (KeyError, IndexError, AttributeError) as e:
                    print(f"Error for segment {start_time}-{end_time}: {e}. Assigning 'unknown' for this segment.")
                    results[(start_time, end_time)] = ['unknown']
                    break  # 오류 발생 시 'unknown' 할당 후 루프 종료
            
                except Exception as e:
                    print(f"Attempt {attempt + 1} for segment {start_time}-{end_time} failed with error: {e}. Retrying...")
                    time.sleep(2 ** attempt)  # 재시도 전에 지수적으로 지연 시간 증가

        # 모든 구간의 분석 결과를 클래스 속성에 저장
        self.gpt_classification_results = results  # 결과를 클래스 속성에 저장

        # 구간에 대한 결과를 반환
        final_results = []
        for (start_time, end_time) in grouped_sentences.keys():
            stage_result = results.get((start_time, end_time), ['unknown'])
            if stage_result == ['unknown']:
                logger.warning(f"Final result for segment {start_time}-{end_time} is unknown.")
            final_results.append(stage_result)

        return final_results


    def determine_final_bloom_stage(self, word, language, start_time, end_time):
        word_based_stage = self.tag_bloom_stage(word, language)
        logger.info(f"Word-based stage for '{word}' at segment {start_time}-{end_time}: {word_based_stage}")

        # 특정 구간의 문장을 가져와서 GPT 분석에 사용
        sentences = self.sentence_data[
            (self.sentence_data['start_time'] == start_time) & 
            (self.sentence_data['end_time'] == end_time)
        ]['word'].values
    
        logger.info(f"Sentences for segment {start_time}-{end_time}: {sentences}")  # 추가 로그
        sentence_based_stage = 'unknown'

        if len(sentences) > 0:
            grouped_sentences = {(start_time, end_time): list(sentences)}
            results = self.gpt_bloom_classification(grouped_sentences)
        
            # 모든 결과 및 필터링 확인
            logger.info(f"GPT classification results for segment {start_time}-{end_time}: {results}")
        
            stages = [stage for sublist in results for stage in sublist if stage != 'unknown']
        
            logger.info(f"Filtered stages for segment {start_time}-{end_time}: {stages}")  # 추가 로그

            if stages:
                stage_counts = Counter(stages)
                sentence_based_stage = stage_counts.most_common(1)[0][0]  # 가장 빈도가 높은 단계 선택
                logger.info(f"Sentence-based stage for segment {start_time}-{end_time}: {sentence_based_stage}")

        # Bloom 단계 우선순위 적용
        if word_based_stage != 'unknown' and sentence_based_stage != 'unknown':
            final_stage = self.choose_better_stage(word_based_stage, sentence_based_stage)
            logger.info(f"Final stage (combined) for segment {start_time}-{end_time}: {final_stage}")
            return final_stage
        elif word_based_stage != 'unknown':
            logger.info(f"Final stage (word-based only) for segment {start_time}-{end_time}: {word_based_stage}")
            return word_based_stage
        else:
            logger.info(f"Final stage (sentence-based only) for segment {start_time}-{end_time}: {sentence_based_stage}")
        return sentence_based_stage


    def choose_better_stage(self, stage1, stage2):
        """비교하여 우선순위가 높은 Bloom 단계 반환"""
        if stage1 not in self.bloom_priority or stage2 not in self.bloom_priority:
            logger.warning(f"Unknown stage encountered: {stage1}, {stage2}")
            return 'unknown'
        better_stage = stage1 if self.bloom_priority[stage1] > self.bloom_priority[stage2] else stage2
        logger.debug(f"Choosing better stage between '{stage1}' and '{stage2}': {better_stage}")
        return better_stage

    def calculate_bloom_distribution(self):
        # 'unknown' bloom_stage 제외한 verb counts 필터링
        filtered_counts = self.verb_counts[self.verb_counts['bloom_stage'] != 'unknown']
        logger.info(f"Filtered verb counts for distribution calculation: {filtered_counts}")

        # GPT 문장 분석 결과에서 구간별 Bloom 단계별 개수 생성
        gpt_stage_data = []
        for (start_time, end_time), stages in self.gpt_classification_results.items():
            for stage in stages:
                if stage != 'unknown':
                    gpt_stage_data.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'bloom_stage': stage
                    })
    
        gpt_stage_counts = pd.DataFrame(gpt_stage_data)
        logger.info(f"GPT stage counts for each segment: {gpt_stage_counts}")

        # verb counts와 GPT stage counts 결합
        combined_counts = pd.concat([filtered_counts, gpt_stage_counts], ignore_index=True)
        logger.info(f"Combined counts (verbs + GPT sentences) for distribution calculation: {combined_counts}")

        # Bloom 단계별로 분포 계산
        self.bloom_distribution = combined_counts.groupby(
             ['start_time', 'end_time', 'bloom_stage']
        ).size().unstack(fill_value=0)

        logger.info("Filtered Bloom stage distribution calculated:")
        logger.debug(self.bloom_distribution)

        # 각 구간에서 가장 빈도가 높은 Bloom 단계 결정
        self.bloom_distribution['decided_stage'] = self.bloom_distribution.idxmax(axis=1)

        logger.info("Decided stages for each segment determined:")
        logger.debug(self.bloom_distribution['decided_stage'])

        return self.bloom_distribution

    def decide_bloom_stage(self, row):
        # 각 구간에서 가장 빈도가 높은 Bloom 단계 결정
        stages = row.drop('unknown').to_dict()
        if not stages:
            logger.debug("No stages found in row; returning 'unknown'")
            return 'unknown'
    
        decided_stage = max(stages, key=lambda stage: (stages[stage], -self.bloom_priority[stage]))
        logger.debug(f"Decided Bloom stage: {decided_stage}")
        return decided_stage

    def merge_segments(self):
        # 동일한 Bloom 단계를 갖는 구간 병합
        merged_segments = []
        start_time, prev_stage, prev_end = None, None, None

        logger.info("Starting segment merging process...")

        for idx, row in self.bloom_distribution.iterrows():
            stage = row['decided_stage']
            current_start = idx[0]  # 'start_time'
            current_end = idx[1]    # 'end_time'

            # 새로운 Bloom 단계가 이전 단계와 다를 때
            if stage != prev_stage:
                # 이전 구간이 존재하면 병합된 구간으로 추가
                if prev_stage is not None:
                    merged_segments.append((start_time, prev_end, prev_stage))
                    logger.info(f"Merged segment: start={start_time}, end={prev_end}, stage={prev_stage}")
                # 새로운 구간 시작
                start_time = current_start

            # 현재 구간의 끝 시간 갱신
            prev_end = current_end
            prev_stage = stage

        # 마지막 구간 추가
        if prev_stage is not None:
            merged_segments.append((start_time, prev_end, prev_stage))
            logger.info(f"Final merged segment: start={start_time}, end={prev_end}, stage={prev_stage}")

        logger.info("Segment merging process completed.")
        logger.debug(f"Merged segments: {merged_segments}")

        return merged_segments

    def analyze_nouns(self, top_n=5):
        nouns = self.word_data[self.word_data['pos'] == 'noun']
        nouns_text = ' '.join(nouns['word'])
        logger.info(f"Noun text concatenated for TF-IDF analysis: {len(nouns_text)} characters")

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([nouns_text])
        feature_names = vectorizer.get_feature_names()
        tfidf_scores = tfidf_matrix.toarray()[0]
        top_n_indices = tfidf_scores.argsort()[-top_n:][::-1]
        top_n_words = [feature_names[i] for i in top_n_indices]
        
        logger.info(f"Top {top_n} nouns by TF-IDF: {top_n_words}")
        return top_n_words

    def format_stage_segments(self, merged_segments):
        stage_dict = {}
        for segment in merged_segments:
            start_time, end_time, stage = segment
            if stage not in stage_dict:
                stage_dict[stage] = []
            stage_dict[stage].append(f"{start_time}-{end_time}")
        formatted_segments = {stage: ', '.join(segments) for stage, segments in stage_dict.items()}
        
        logger.info(f"Formatted stage segments: {formatted_segments}")
        return formatted_segments


#그래프 객체 생성(디자인 수정가능 여기를 확인하세요!)
import plotly.express as px
import plotly.graph_objects as go

# 그래프 객체 생성(디자인 수정가능 여기를 확인하세요!)
class BloomGraphRenderer:
    def __init__(self, bloom_distribution, merged_segments):
        self.bloom_distribution = bloom_distribution
        self.merged_segments = merged_segments

        print(self.merged_segments)  # 데이터 구조 확인

    def plot_donut_chart(self):
        # 각 'decided_stage'의 빈도수를 계산
        bloom_counts = self.bloom_distribution['decided_stage'].value_counts().reset_index()
        bloom_counts.columns = ['bloom_stage', 'counts']
        bloom_counts = bloom_counts[bloom_counts['bloom_stage'] != 'unknown']

        color_map = {
            'remember': '#8290c4', 'understand': '#88c1e8',
            'apply': '#74ac80', 'analyze': '#b1d984',
            'evaluate': '#fae373', 'create': '#fb8976'
        }

        fig = px.pie(
            bloom_counts, names='bloom_stage', values='counts', hole=0.5,
            color='bloom_stage', color_discrete_map=color_map
        )

        # 그래프 레이아웃 설정
        fig.update_layout(
            width=500,
            height=500,
            paper_bgcolor='rgba(0, 0, 0, 0)',  # 완전 투명 배경
            plot_bgcolor='rgba(0, 0, 0, 0)',   # 그래프 배경 투명
            font=dict(
                family='Arial',      # 글꼴체 설정
                color='#2a3f5f'      # 글자색
            ),
            title_font=dict(
                family='Arial',      # 제목 글꼴체 설정
                color='#2a3f5f'      # 제목 글자색
            ),
        )
        
        return fig

    def plot_dot_graph(self):
        # Bloom 단계와 매핑
        bloom_stage_mapping = {
            'remember': 1,
            'understand': 2,
            'apply': 3,
            'analyze': 4,
            'evaluate': 5,
            'create': 6
        }

        # 각 Bloom 단계에 대한 색상 맵
        color_map = {
            'remember': '#8290c4',
            'understand': '#88c1e8',
            'apply': '#74ac80',
            'analyze': '#b1d984',
            'evaluate': '#fae373',
            'create': '#fb8976'
        }

        # 그래프에 사용할 데이터 초기화
        x_values = []
        y_values = []
        colors = []

        # 겹치는 구간을 저장하기 위한 딕셔너리
        active_stages = {}

        for segment in self.merged_segments:
            start, end, stage = segment[0], segment[1], segment[2]
            numeric_stage = bloom_stage_mapping.get(stage.lower())
    
            if numeric_stage is not None:
                # 겹치는 구간 처리
                for time in range(start, end + 1, 60):  # 60초 간격으로 나눔
                    if time not in active_stages or active_stages[time] < numeric_stage:
                        active_stages[time] = numeric_stage  # 더 높은 단계로 업데이트

        # active_stages를 사용하여 x, y, color 값을 설정
        for time, stage in active_stages.items():
            x_values.append(time)
            y_values.append(stage)
            colors.append(color_map[list(bloom_stage_mapping.keys())[stage - 1]])  # 각 단계에 맞는 색상


        # 도트 그래프 데이터 구성
        dot_trace = go.Scatter(
            x=x_values,
            y=y_values,
            mode='markers',
            marker=dict(size=10, color=colors),
            name='Bloom Stages'
        )

        layout = go.Layout(
            title='Bloom Stages Over Time', 
            xaxis_title='Time (seconds)', 
            yaxis_title='Bloom Stage (numeric)',
            yaxis=dict(
                tickvals=list(bloom_stage_mapping.values()),  # 모든 Bloom 단계 값
                ticktext=list(bloom_stage_mapping.keys()),  # 모든 Bloom 단계 이름
                range=[0.5, 6.5]  # y축 범위를 설정하여 모든 단계가 보이도록 함
            ),
            height=400,  # 높이 설정
            width=600,   # 너비 설정
            paper_bgcolor='rgba(0, 0, 0, 0)',  # 완전 투명 배경
            plot_bgcolor='rgba(0, 0, 0, 0)',   # 그래프 배경 투명
            font=dict(
                family='Arial',      # 글꼴체 설정
                color='#2a3f5f'      # 글자색
            ),
            title_font=dict(
                family='Arial',      # 제목 글꼴체 설정
                color='#2a3f5f'      # 제목 글자색
            ),
        )

        # Figure 객체 생성 및 반환
        fig = go.Figure(data=[dot_trace], layout=layout)
        return fig

    
#분석기 실행
def run_analysis(request, video_id):
    db = get_mongo_connection()
    learning_video_collection = db['BloomHub_learningvideo']
    analysis_result_collection = db['BloomHub_analysisresult']

    # LearningVideo에서 비디오 정보 가져오기
    video = learning_video_collection.find_one({"vid": video_id})
    if not video:
        return JsonResponse({"success": False, "error": "Video not found."})

    # 분석 결과가 이미 존재하는지 확인
    existing_analysis = analysis_result_collection.find_one({"video_id": video_id})
    if existing_analysis:
        # 이미 분석 결과가 존재하는 경우
        response_data = {
            "success": True,
            "top_nouns": existing_analysis.get("top_nouns"),
            "stage_segments": existing_analysis.get("bloom_stage_segments"),
            "donut_chart": existing_analysis.get("donut_chart"),
            "dot_graph": existing_analysis.get("dot_chart")
        }
        logger.info("Existing analysis found. Returning existing results.")
        return JsonResponse(response_data)

    # 새로 분석 시작
    language = video.get("std_lang")
    analyzer = BloomAnalysisWithGPTandDictionary(video_id, language)

    try:
        logger.info("Processing verbs...")
        analyzer.process_verbs()
        logger.info("Calculating bloom distribution...")
        analyzer.calculate_bloom_distribution()
        logger.info("Merging segments...")
        merged_segments = analyzer.merge_segments()

        logger.info("Formatting stage segments...")
        stage_segments = analyzer.format_stage_segments(merged_segments)
        logger.info("Analyzing nouns...")
        top_nouns = analyzer.analyze_nouns()

        # 그래프 생성
        logger.info("Generating donut chart...")
        graph_renderer = BloomGraphRenderer(analyzer.bloom_distribution, merged_segments)
        donut_chart = graph_renderer.plot_donut_chart()
        
        logger.info("Generating dot graph...")
        dot_graph = graph_renderer.plot_dot_graph()

        logger.debug(f"Donut chart data: {pio.to_json(donut_chart)}")
        logger.debug(f"Dot graph data: {pio.to_json(dot_graph)}")

        # JSON 변환 후 MongoDB에 저장
        analysis_result = {
            "video_id": video_id,
            "bloom_stage_segments": stage_segments,
            "top_nouns": top_nouns,
            "donut_chart": pio.to_json(donut_chart),
            "dot_chart": pio.to_json(dot_graph)
        }
        analysis_result_collection.insert_one(analysis_result)

        response_data = {
            "success": True,
            "top_nouns": top_nouns,
            "stage_segments": stage_segments,
            "donut_chart": analysis_result["donut_chart"],
            "dot_graph": analysis_result["dot_chart"]
        }
        logger.info("Analysis completed successfully.")

    except Exception as e:
        logger.error(f"An error occurred during analysis: {str(e)}")
        response_data = {"success": False, "error": str(e)}

    logger.debug(f"Response data: {response_data}")
    return JsonResponse(response_data)

# 분석결과 저장버튼함수
@csrf_exempt
# 분석 결과 저장 함수 예시
def save_analysis_result(request):
    if request.method == "POST":
        data = json.loads(request.body)
        video_id = data.get("video_id")
        bloom_stage_segments = data.get("bloom_stage_segments")
        top_nouns = data.get("top_nouns")
        donut_chart = data.get("donut_chart")
        dot_chart = data.get("dot_chart")

        try:
            # MongoDB 연결
            db = get_mongo_connection()
            analysis_result_collection = db['BloomHub_analysisresult']

            # 분석 결과가 이미 존재하는지 확인
            existing_analysis = analysis_result_collection.find_one({"video_id": video_id})
            if existing_analysis:
                existing_analysis["_id"] = str(existing_analysis["_id"])
                return JsonResponse({"success": True, "result": existing_analysis})  # 이미 존재하는 경우 success를 True로 설정

            # 새로운 분석 결과 저장
            analysis_result = {
                "video_id": video_id,
                "bloom_stage_segments": bloom_stage_segments,
                "top_nouns": top_nouns,
                "donut_chart": donut_chart,
                "dot_chart": dot_chart,
                "learning_status": True
            }
            result = analysis_result_collection.insert_one(analysis_result)
            analysis_result["_id"] = str(result.inserted_id)

            return JsonResponse({"success": True, "result": analysis_result})

        except Exception as e:
            error_message = f"Error saving analysis result: {str(e)}\nTraceback: {traceback.format_exc()}"
            logger.error(error_message)
            return JsonResponse({"success": False, "error": error_message})

    return JsonResponse({"success": False, "error": "Invalid request."})


#분석결과 불러오기 함수
def get_analysis_result(request, video_id):
    try:
        analysis_result = AnalysisResult.objects.get(video__vid=video_id)
        
        response_data = {
            "success": True,
            "bloom_stage_segments": analysis_result.bloom_stage_segments,
            "top_nouns": analysis_result.top_nouns,
            "donut_chart": analysis_result.donut_chart,
            "dot_chart": analysis_result.dot_chart
        }
    except AnalysisResult.DoesNotExist:
        response_data = {"success": False, "error": "분석 결과가 존재하지 않습니다."}
    except Exception as e:
        response_data = {"success": False, "error": str(e)}

    return JsonResponse(response_data)






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

#########마이페이지 이메일 띄우기
@login_required
def get_user_info(request):
    user = request.user
    last_login = user.last_login

    if last_login:
        # 서버 시간(UTC)을 로컬 시간으로 변환
        local_last_login = timezone.localtime(last_login)
        # 24시간 형식으로 포맷
        last_login_str = local_last_login.strftime("%Y-%m-%d %H:%M:%S")
    else:
        last_login_str = "No login data"

    return JsonResponse({
        'email': user.email,
        'last_login': last_login_str
    })

@login_required
def reset_password(request):
    if request.method == "POST":
        user = request.user
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # 입력된 비밀번호 확인
        if not new_password or not confirm_password:
            return JsonResponse({'success': False, 'message': 'Please fill in all password fields.'})
        
        if new_password != confirm_password:
            return JsonResponse({'success': False, 'message': 'Passwords do not match.'})
        
        if user:
            user.set_password(new_password)
            user.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'message': 'User not found.'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

@login_required
def change_email(request):
    if request.method == "POST":
        user = request.user
        new_email = request.POST.get('email')
        
        # 이메일 필드가 비어 있는지 확인
        if not new_email:
            return JsonResponse({'success': False, 'message': 'Please enter a valid email address.'})
        
        # 사용자 이메일 변경
        if user:
            user.email = new_email
            user.save()
            return JsonResponse({'success': True, 'message': 'Email has been updated.'})
        else:
            return JsonResponse({'success': False, 'message': 'User not found.'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

@login_required
def check_old_password(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        # 인증된 사용자의 기존 비밀번호와 비교
        if request.user.check_password(new_password):
            return JsonResponse({'is_same_as_old': True})
        else:
            return JsonResponse({'is_same_as_old': False})

    return JsonResponse({'error': 'Invalid request method'}, status=400)


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