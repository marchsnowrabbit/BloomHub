from youtube_transcript_api import YouTubeTranscriptApi
from konlpy.tag import Okt
import pandas as pd
import urllib.parse
import urllib.request
import json

class KoreanScriptExtractor:
    def __init__(self, vid, setTime, wikiUserKey, NUM_OF_WORDS=5):
        self.vid = vid
        self.setTime = setTime
        self.wikiUserKey = wikiUserKey
        self.NUM_OF_WORDS = NUM_OF_WORDS
        self.segments = []
        self.stopwords = self.load_stopwords()
        self.okt = Okt()

    def load_stopwords(self):
        with open('stopwords-ko.txt', 'r', encoding='utf-8') as file:
            return set(line.strip() for line in file)

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
            analyzed_segment = self.okt.pos(segment['text'])
            nouns = [word for word, pos in analyzed_segment if pos.startswith('N')]
            verbs = [word for word, pos in analyzed_segment if pos.startswith('V')]
            filtered_nouns = [word for word in nouns if word not in self.stopwords]
            filtered_verbs = [word for word in verbs if word not in self.stopwords]
            segment['nouns'] = filtered_nouns
            segment['verbs'] = filtered_verbs
            print("Segment Nouns (after removing stopwords):", filtered_nouns)
            print("Segment Verbs (after removing stopwords):", filtered_verbs)

    def url_to_wiki(self):
        self.extract()
        self.konlpy_analysis()
        if not self.scriptData:
            return pd.DataFrame()

        results = []
        for segment in self.segments:
            wikifier_result = self.call_wikifier(segment['text'])
            for res in wikifier_result:
                res['segment'] = segment
            results.extend(wikifier_result)

        wiki_data = pd.DataFrame()
        for result in results:
            segment = result.pop('segment')
            for noun in segment['nouns']:
                result_copy = result.copy()
                result_copy['word'] = noun
                result_copy['pos'] = 'noun'
                wiki_data = pd.concat([wiki_data, pd.DataFrame([result_copy])], ignore_index=True)
            for verb in segment['verbs']:
                result_copy = result.copy()
                result_copy['word'] = verb
                result_copy['pos'] = 'verb'
                wiki_data = pd.concat([wiki_data, pd.DataFrame([result_copy])], ignore_index=True)

        return wiki_data

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

if __name__ == "__main__":
    extractor = KoreanScriptExtractor(vid="유튜브 영상 ID", setTime=600, wikiUserKey="Your_Wikifier_API_Key")
    wiki_data = extractor.url_to_wiki()
    print(wiki_data)
