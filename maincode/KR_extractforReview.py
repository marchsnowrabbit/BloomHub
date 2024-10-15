from youtube_transcript_api import YouTubeTranscriptApi
from konlpy.tag import Okt
import pandas as pd
import urllib.parse
import urllib.request
import json
import concurrent.futures
import re

class KoreanScriptExtractor:
    # 클래스 초기화: YouTube 영상 ID, 시간 설정, 위키피디어 API 사용자 키, 그리고 분석할 단어 수를 설정
    def __init__(self, vid, setTime, wikiUserKey, NUM_OF_WORDS=5):
        self.vid = vid
        self.setTime = setTime
        self.wikiUserKey = wikiUserKey
        self.NUM_OF_WORDS = NUM_OF_WORDS
        self.segments = []  # 자막을 시간대로 분할한 세그먼트 저장
        self.stopwords = self.load_stopwords()  # 불용어 리스트 로드
        self.okt = Okt()  # Okt 형태소 분석기 초기화
        self.video_title = self.get_video_title()  # 유튜브 제목 가져오기

    # 불용어 파일 로드
    def load_stopwords(self):
        with open('stopwords-ko.txt', 'r', encoding='utf-8') as file:
            return set(line.strip() for line in file)

    # 유튜브 영상 제목을 가져오는 함수
    def get_video_title(self):
        video_id = self.vid.split("v=")[1]  # YouTube URL에서 영상 ID 추출
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        title = re.search(r'<title>(.*?)</title>', html).group(1)  # HTML에서 제목 추출
        return title.replace(' - YouTube', '').strip()  # 불필요한 텍스트 제거 후 반환

    # 한국어 자막 추출 및 세그먼트화
    def extract(self):
        video_id = self.vid.split("v=")[1]
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        self.scriptData = None

        # 한국어 자막을 찾음
        for transcript in transcript_list:
            if transcript.language_code == 'ko':
                self.scriptData = transcript.fetch()  # 자막 데이터 가져오기
                break

        # 자막이 없을 경우 메시지 출력 후 종료
        if not self.scriptData:
            print("한국어 자막이 없습니다.")
            return

        # 자막을 60초 단위로 분할
        segment_duration = 60
        start_time = 0
        end_time = segment_duration
        segment_texts = []

        for segment in self.scriptData:
            # 자막이 현재 세그먼트 시간 범위 내에 있는 경우
            if start_time <= segment['start'] < end_time:
                segment_texts.append(segment['text'])
            # 세그먼트 시간이 넘어간 경우 새로운 세그먼트 추가
            elif segment['start'] >= end_time:
                self.add_segment(segment_texts, start_time, end_time)  # 세그먼트 추가
                segment_texts = [segment['text']]
                start_time = end_time
                end_time += segment_duration

        # 마지막 세그먼트 추가
        if segment_texts:
            self.add_segment(segment_texts, start_time, end_time)

    # 세그먼트 데이터를 추가하는 함수
    def add_segment(self, texts, start_time, end_time):
        segment_data = {
            "text": " ".join(texts),  # 텍스트를 공백으로 결합
            "start_time": start_time,
            "end_time": end_time
        }
        self.segments.append(segment_data)

    # 형태소 분석을 통해 명사와 동사를 추출하는 함수
    def konlpy_analysis(self):
        for segment in self.segments:
            analyzed_segment = self.okt.pos(segment['text'], stem=True)  # 형태소 분석 및 어간 추출
            nouns = [word for word, pos in analyzed_segment if pos.startswith('N')]  # 명사 추출
            verbs = [word for word, pos in analyzed_segment if pos.startswith('V')]  # 동사 추출
            filtered_nouns = [word for word in nouns if word not in self.stopwords]  # 불용어 제거
            filtered_verbs = [word for word in verbs if word not in self.stopwords]  # 불용어 제거
            segment['nouns'] = filtered_nouns
            segment['verbs'] = filtered_verbs

    # 위키피디어 API 호출 및 데이터프레임 생성
    def url_to_wiki(self):
        self.extract()  # 자막 추출
        self.konlpy_analysis()  # 형태소 분석
        if not self.scriptData:
            return pd.DataFrame()

        results = []
        # 병렬 처리로 세그먼트 텍스트에 대해 위키피디아 API 호출
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_segment = {executor.submit(self.call_wikifier, segment['text']): segment for segment in self.segments}
            for future in concurrent.futures.as_completed(future_to_segment):
                segment = future_to_segment[future]
                try:
                    wikifier_result = future.result()  # API 결과 받아오기
                    for res in wikifier_result:
                        res['segment'] = segment
                    results.extend(wikifier_result)  # 결과 리스트에 추가
                except Exception as e:
                    print(f"Error during Wikifier API call: {e}")

        # 결과 처리 및 데이터프레임 생성
        wiki_data = []
        for result in results:
            segment = result.pop('segment')
            # 명사 데이터 추가
            for noun in segment['nouns']:
                result_copy = result.copy()
                result_copy['word'] = noun
                result_copy['pos'] = 'noun'
                result_copy['start_time'] = segment['start_time']
                result_copy['end_time'] = segment['end_time']
                result_copy['title'] = self.video_title
                wiki_data.append(result_copy)
            # 동사 데이터 추가
            for verb in segment['verbs']:
                result_copy = result.copy()
                result_copy['word'] = verb
                result_copy['pos'] = 'verb'
                result_copy['start_time'] = segment['start_time']
                result_copy['end_time'] = segment['end_time']
                result_copy['title'] = self.video_title
                wiki_data.append(result_copy)

        df = pd.DataFrame(wiki_data)
        df.drop(columns=['segment_text'], inplace=True, errors='ignore')  # 필요없는 열 제거
        return df

    # Wikifier API 호출 함수
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

# 최종 결과는 타이틀제목/url/페이지 랭크/단어/품사/시작시간/종료시간의 형태로 저장됨. csv 파일로 저장.
# 유저키는 작성자의 것으로 사용. eqhfcdvhiwoikruteziguewrqhnkqn
# 영상 링크는 사용자로부터 입력받을 예정.
# 5분 기준으로 처리할 경우 약 38초 소요됨 (명사, 동사 분류 포함).

if __name__ == "__main__":
    # KoreanScriptExtractor 클래스 인스턴스 생성 및 위키 데이터 저장
    extractor = KoreanScriptExtractor(vid="https://www.youtube.com/watch?v=3R6vFdb7YI4", setTime=6000, wikiUserKey="eqhfcdvhiwoikruteziguewrqhnkqn")
    wiki_data = extractor.url_to_wiki()
    wiki_data.to_csv('or1.csv')  # 결과를 CSV 파일로 저장
    print(wiki_data)
