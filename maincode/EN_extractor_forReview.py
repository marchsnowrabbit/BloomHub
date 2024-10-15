import pandas as pd
import spacy  # 자연어 처리 라이브러리
from youtube_transcript_api import YouTubeTranscriptApi  # YouTube 동영상 자막을 가져오는 라이브러리
import urllib.parse  # URL 인코딩을 위한 모듈
import urllib.request  # 웹 요청을 처리하는 모듈
import json  # JSON 데이터를 처리하는 모듈
import concurrent.futures  # 비동기 작업 처리를 위한 모듈
import re  # 정규 표현식을 사용한 패턴 매칭
import nltk  # 자연어 처리를 위한 도구, 여기서는 불용어(stopwords) 처리를 위해 사용

# # nltk 불용어 다운로드 (최초 실행 시 한 번 필요)
# nltk.download('stopwords')

# 영어 스크립트 추출 클래스
class EnglishScriptExtractor:
    def __init__(self, vid, setTime, wikiUserKey, NUM_OF_WORDS=5):
        self.vid = vid  # YouTube 동영상 URL
        self.setTime = setTime  # 설정된 시간 간격 (초 단위)
        self.wikiUserKey = wikiUserKey  # 위키파이어 API 호출을 위한 사용자 키
        self.NUM_OF_WORDS = NUM_OF_WORDS  # 분석할 단어 수
        self.segments = []  # 동영상 자막을 시간별로 나눈 세그먼트
        self.nlp = spacy.load('en_core_web_sm')  # spacy를 사용한 영어 자연어 처리 모델 로드
        self.stop_words = set(stopwords.words('english'))  # nltk를 사용한 영어 불용어 목록
        self.video_title = self.get_video_title()  # 동영상 제목을 가져옴

    # YouTube 동영상의 제목을 가져오는 함수
    def get_video_title(self):
        video_id = self.vid.split("v=")[1]  # URL에서 동영상 ID 추출
        url = f"https://www.youtube.com/watch?v={video_id}"  # YouTube 동영상 페이지 URL
        headers = {'User-Agent': 'Mozilla/5.0'}  # 웹 요청 시 브라우저 헤더 추가
        req = urllib.request.Request(url, headers=headers)  # 요청 객체 생성
        response = urllib.request.urlopen(req)  # 웹 요청 실행
        html = response.read().decode('utf-8')  # 응답을 UTF-8로 디코딩
        title = re.search(r'<title>(.*?)</title>', html).group(1)  # HTML에서 <title> 태그의 내용을 정규표현식으로 추출
        return title.replace(' - YouTube', '').strip()  # ' - YouTube' 제거 후 반환

    # 자막을 추출하는 함수
    def extract(self):
        video_id = self.vid.split("v=")[1]  # 동영상 ID 추출
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)  # 자막 리스트 가져오기
        self.scriptData = None  # 자막 데이터를 저장할 변수
        for transcript in transcript_list:
            if transcript.language_code == 'en':  # 영어 자막을 찾으면
                self.scriptData = transcript.fetch()  # 자막 데이터 추출
                break

        if not self.scriptData:  # 영어 자막이 없을 경우
            print("This video doesn't have english scripts")  # 오류 메시지 출력
            return

        segment_duration = 60  # 자막 세그먼트 길이 설정 (60초)
        start_time = 0  # 시작 시간 초기화
        end_time = segment_duration  # 종료 시간 설정
        segment_texts = []  # 세그먼트에 들어갈 텍스트 리스트

        for segment in self.scriptData:
            if start_time <= segment['start'] < end_time:  # 세그먼트 시간이 설정된 시간 범위에 있을 경우
                segment_texts.append(segment['text'])  # 텍스트 추가
            elif segment['start'] >= end_time:  # 다음 세그먼트로 넘어가면
                self.add_segment(segment_texts, start_time, end_time)  # 세그먼트 추가
                segment_texts = [segment['text']]  # 새로운 세그먼트 시작
                start_time = end_time  # 시작 시간 업데이트
                end_time += segment_duration  # 종료 시간 업데이트

        if segment_texts:  # 마지막 세그먼트 추가
            self.add_segment(segment_texts, start_time, end_time)

    # 세그먼트를 추가하는 함수
    def add_segment(self, texts, start_time, end_time):
        segment_data = {
            "text": " ".join(texts),  # 텍스트 합치기
            "start_time": start_time,  # 세그먼트 시작 시간
            "end_time": end_time  # 세그먼트 종료 시간
        }
        self.segments.append(segment_data)  # 세그먼트 리스트에 추가

    # Spacy를 사용해 텍스트에서 명사와 동사 추출
    def spacy_analysis(self):
        for segment in self.segments:
            doc = self.nlp(segment['text'])  # 텍스트를 Spacy로 분석
            nouns = [token.text for token in doc if token.pos_ == 'NOUN' and token.text.lower() not in self.stop_words]  # 명사 추출
            verbs = [token.lemma_ for token in doc if token.pos_ == 'VERB' and token.lemma_.lower() not in self.stop_words]  # 동사 추출 (원형으로)
            segment['nouns'] = nouns  # 명사 리스트 저장
            segment['verbs'] = verbs  # 동사 리스트 저장

    # 추출된 데이터를 위키파이어 API를 통해 분석하고, 결과를 DataFrame으로 반환
    def url_to_wiki(self):
        self.extract()  # 자막 추출
        self.spacy_analysis()  # 명사/동사 분석
        if not self.scriptData:  # 자막 데이터가 없으면 빈 DataFrame 반환
            return pd.DataFrame()

        results = []  # 결과 저장 리스트
        with concurrent.futures.ThreadPoolExecutor() as executor:  # 비동기 작업 실행
            future_to_segment = {executor.submit(self.call_wikifier, segment['text']): segment for segment in self.segments}
            for future in concurrent.futures.as_completed(future_to_segment):
                segment = future_to_segment[future]
                try:
                    wikifier_result = future.result()  # 위키파이어 결과 저장
                    for res in wikifier_result:
                        res['segment'] = segment  # 세그먼트 정보 추가
                    results.extend(wikifier_result)  # 결과 리스트에 추가
                except Exception as e:
                    print(f"Error during Wikifier API call: {e}")  # API 호출 에러 처리

        wiki_data = []  # 최종 위키 데이터 저장 리스트
        for result in results:
            segment = result.pop('segment')
            for noun in segment['nouns']:  # 명사별로 결과 저장
                result_copy = result.copy()
                result_copy['word'] = noun
                result_copy['pos'] = 'noun'
                result_copy['start_time'] = segment['start_time']
                result_copy['end_time'] = segment['end_time']
                result_copy['title'] = self.video_title
                wiki_data.append(result_copy)
            for verb in segment['verbs']:  # 동사별로 결과 저장
                result_copy = result.copy()
                result_copy['word'] = verb
                result_copy['pos'] = 'verb'
                result_copy['start_time'] = segment['start_time']
                result_copy['end_time'] = segment['end_time']
                result_copy['title'] = self.video_title
                wiki_data.append(result_copy)

        df = pd.DataFrame(wiki_data)  # DataFrame으로 변환
        df.drop(columns=['segment_text'], inplace=True, errors='ignore')  # 불필요한 열 삭제
        return df  # 최종 DataFrame 반환

    # 위키파이어 API 호출 함수
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

# 최종 결과는 타이틀 제목/url/페이지 랭크/단어/품사/시작 시간/종료 시간의 형태로 저장됨. csv 파일로 저장
if __name__ == "__main__":
    newEx = EnglishScriptExtractor(vid="https://www.youtube.com/watch?v=eWRfhZUzrAc&list=PLWKjhJtqVAbnqBxcdjVGgT3uVR10bzTEB", setTime=18000, wikiUserKey="eqhfcdvhiwoikruteziguewrqhnkqn")
    wiki_data = newEx.url_to_wiki()  # 위키 데이터 추출
    wiki_data.to_csv('new.csv')  # CSV 파일로 저장
    print(wiki_data)  # 결과 출력
