from youtube_transcript_api import YouTubeTranscriptApi
from konlpy.tag import Okt
import pandas as pd
import urllib.parse
import urllib.request
import json
import concurrent.futures
import re

class KoreanScriptExtractor:
    def __init__(self, vid, setTime, wikiUserKey, NUM_OF_WORDS=5):
        self.vid = vid
        self.setTime = setTime
        self.wikiUserKey = wikiUserKey
        self.NUM_OF_WORDS = NUM_OF_WORDS
        self.segments = []
        self.stopwords = self.load_stopwords()
        self.okt = Okt()
        self.video_title = self.get_video_title()

    def load_stopwords(self):
        with open('KR_bloom_dictionary/stopwords-ko.txt', 'r', encoding='utf-8') as file:
            return set(line.strip() for line in file)

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
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        self.scriptData = None
        for transcript in transcript_list:
            if transcript.language_code == 'ko':
                self.scriptData = transcript.fetch()
                break

        if not self.scriptData:
            print("한국어 자막이 없습니다.")
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

    def konlpy_analysis(self):
        for segment in self.segments:
            analyzed_segment = self.okt.pos(segment['text'], stem=True)
            nouns = [ word for word, pos in analyzed_segment if pos.startswith('N')]
            verbs = [ word for word, pos in analyzed_segment if pos.startswith('V')]
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

#최종 결과는 타이틀제목/url/페이지 랭크/단어/품사 /시작시간/ 종료시간 의 형태로 저장됨. csv
# 유저키는 일단 작성자의 것. 즉 eqhfcdvhiwoikruteziguewrqhnkqn 로 사용함
# 영상링크는 사용자에게 받아 사용 예정
# 5분 기준 -> 38초 정도 소요 됨(명사,동사 분류)
if __name__ == "__main__":
    extractor = KoreanScriptExtractor(vid="https://www.youtube.com/watch?v=3R6vFdb7YI4", setTime=6000, wikiUserKey="eqhfcdvhiwoikruteziguewrqhnkqn")
    wiki_data = extractor.url_to_wiki()
    wiki_data.to_csv('or1.csv')
    print(wiki_data)
