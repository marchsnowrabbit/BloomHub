import pandas as pd
import spacy
from youtube_transcript_api import YouTubeTranscriptApi
import urllib.parse
import urllib.request
import json
import concurrent.futures
import re
import nltk
from nltk.corpus import stopwords

# # nltk 불용어 다운로드 (최초 실행 시 한 번 필요)
# nltk.download('stopwords')

class EnglishScriptExtractor:
    def __init__(self, vid, setTime, wikiUserKey, NUM_OF_WORDS=5):
        self.vid = vid
        self.setTime = setTime
        self.wikiUserKey = wikiUserKey
        self.NUM_OF_WORDS = NUM_OF_WORDS
        self.segments = []
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
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        self.scriptData = None
        for transcript in transcript_list:
            if transcript.language_code == 'en':
                self.scriptData = transcript.fetch()
                break

        if not self.scriptData:
            print("This video doesn't have english scripts")
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

# 최종 결과는 타이틀 제목/url/페이지 랭크/단어/품사/시작 시간/종료 시간의 형태로 저장됨. csv
# 유저키는 작성자의 것으로 사용됨. 즉 eqhfcdvhiwoikruteziguewrqhnkqn 로 사용함
# 영상 링크는 사용자에게 받아 사용 예정
# 5분 기준 -> 38초 정도 소요 됨(명사,동사 분류)
if __name__ == "__main__":
    extractor = EnglishScriptExtractor(vid="https://www.youtube.com/watch?v=6i3EGqOBRiU&list=PLdo5W4Nhv31bZSiqiOL5ta39vSnBxpOPT", setTime=600, wikiUserKey="eqhfcdvhiwoikruteziguewrqhnkqn")
    wiki_data = extractor.url_to_wiki()
    wiki_data.to_csv('en.csv')
    print(wiki_data)
