from youtube_transcript_api import YouTubeTranscriptApi
from konlpy.tag import Okt
import pandas as pd


class KoreanScriptExtractor:
    def __init__(self, vid, setTime, NUM_OF_WORDS=5):
        self.vid = vid
        self.segments = []  # 세그먼트 및 시간 정보를 저장할 리스트
        self.setTime = setTime
        self.NUM_OF_WORDS = NUM_OF_WORDS

    # 유튜브 스크립트 추출
    def extract(self):
        video_id = self.vid.split("v=")[1]
        
        # 유튜브 자막 추출
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        for transcript in transcript_list:
            if transcript.language_code == 'ko':  # 한국어 자막만 처리
                self.scriptData = transcript.fetch()
                break

        if not self.scriptData:
            print("한국어 자막이 없습니다.")
            return

        print("Extracted Korean transcript")

        # 세그먼트를 1분 단위로 나누어 세그먼트와 시간 정보 저장
        segment_duration = 60  # 1분 = 60초
        start_time = 0
        end_time = segment_duration
        segment_texts = []
        for segment in self.scriptData:
            if segment['start'] >= start_time and segment['start'] < end_time:
                segment_texts.append(segment['text'])
            elif segment['start'] >= end_time:
                segment_data = {
                    "text": " ".join(segment_texts),
                    "start_time": start_time,
                    "end_time": end_time
                }
                self.segments.append(segment_data)
                segment_texts = [segment['text']]
                start_time = end_time
                end_time += segment_duration

        # 마지막 세그먼트가 남아있는 경우 추가
        if segment_texts:
            segment_data = {
                "text": " ".join(segment_texts),
                "start_time": start_time,
                "end_time": end_time
            }
            self.segments.append(segment_data)

        print("Extracted {} segments".format(len(self.segments)))

    # Konlpy를 사용하여 형태소 분석 및 품사 태깅
    def konlpy_analysis(self):
        okt = Okt()  # Konlpy의 Okt 형태소 분석기 인스턴스 생성

        for segment in self.scriptData:
            analyzed_segment = okt.pos(segment)
            nouns = [word for word, pos in analyzed_segment if pos.startswith('N')]
            verbs = [word for word, pos in analyzed_segment if pos.startswith('V')]
            filtered_nouns = [self.remove_stopwords(word) for word in nouns]
            filtered_verbs = [self.remove_stopwords(word) for word in verbs]
            print("Segment Nouns (after removing stopwords):", filtered_nouns)
            print("Segment Verbs (after removing stopwords):", filtered_verbs)

    # 불용어 제거
    def remove_stopwords(self, text):
        with open('stopwords-ko.txt', 'r', encoding='utf-8') as file:
            stopwords = set(line.strip() for line in file)
        return " ".join(word for word in text.split() if word not in stopwords)

    # 세그먼트를 Wikifier API로 호출하여 개념 추출하고 결과를 DataFrame으로 반환
    def url_to_wiki(self):
        self.extract()

        results = []
        for text in self.scriptData:
            results.append(self.call_wikifier(text=text, numberOfKCs=self.NUM_OF_WORDS))

        wiki_data = pd.DataFrame()
        seg_no = 1

        for seg_item in results:
            seg_df = pd.DataFrame(seg_item)
            seg_df['seg_no'] = seg_no
            seg_df['understand'] = 0
            wiki_data = pd.concat([wiki_data, seg_df])
            seg_no = seg_no + 1

        wiki_data.index = range(len(wiki_data))
        return wiki_data

    # Wikifier API를 사용하여 개념 추출
    def call_wikifier(self, text, lang="ko", threshold=0.8, numberOfKCs=10):
        # 여기에는 Wikifier API 호출 코드를 넣으세요.
        pass

if __name__ == "__main__":
    extractor = KoreanScriptExtractor(vid="유튜브 영상 ID", setTime=600)
    wiki_data = extractor.url_to_wiki()
    print(wiki_data)
