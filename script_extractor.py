from konlpy.tag import Okt
from konlpy.tag import Kkma 
from konlpy.tag import Komoran
import pandas as pd
from youtube_transcript_api import YouTubeTranscriptApi

#비디오 자막출력부
video_id = "xNMGGQIU8FU&list=PLMsa_0kAjjrdiwQykI8eb3H4IRxLTqCnP&index=3"  # 다운로드하고자 하는 YouTube 비디오 ID
transcript_list = YouTubeTranscriptApi.list_transcripts("xNMGGQIU8FU&list=PLMsa_0kAjjrdiwQykI8eb3H4IRxLTqCnP&index=3")

# 한국어로 된 자막을 선택
transcript = transcript_list.find_transcript(['ko'])

if transcript:
    with open("subtitles.txt", "w", encoding='utf-8') as f:
        for caption in transcript.fetch():
            text = caption['text']
            f.write(f"{text}\n")
else:
    print("한국어 자막을 찾을 수 없습니다.")

# 추출해보기
# 1. 불용어 제거 -> 명확한 토큰화 // 파일 받아와서이용 https://github.com/stopwords-iso/stopwords-ko?tab=readme-ov-file
# 2. 명사 추출
# 3. 동사 추출

#불용어 제거
def removestopwords(text, stop_words):
    okt = Okt()
    text = text.replace('#', '')
    tokens = okt.morphs(text)
    tokens = [token for token in tokens if token not in stop_words]
    return ' '.join(tokens)
# 불용어 집합(Set)을 파일로부터 읽어오기
with open('stopwords-ko.txt', 'r', encoding='utf-8') as file:
    stop_words = set(line.strip() for line in file)
# 원본자막
with open('subtitles.txt', 'r') as f:
    file_data = f.read()
# 텍스트에서 불용어 제거
filtered_sentences = removestopwords(file_data,stop_words)
print(filtered_sentences)

#한글자인건 버리기
def filter_words(words):
    filtered_words = []
    for word in words:
        if len(word) > 1: 
            filtered_words.append(word)
    return filtered_words

#코모란 명사만
komo = Komoran()
filtered_nouns = filter_words(komo.nouns(filtered_sentences))
print(filtered_nouns)
#kkma 명사만
kkma = Kkma()
filtered_nouns= filter_words(kkma.nouns(filtered_sentences))
print(filtered_nouns)

#형태소코모란
morphs = komo.pos(filtered_sentences)
nouns = [word for word, pos in morphs if pos.startswith('N')]
verbs = [word for word, pos in morphs if pos.startswith('V')]
nouns = filter_words(nouns)
verbs = filter_words(verbs)
print("명사:", nouns)
print("동사:", verbs)

#형태소 kkma
morphs= kkma.pos(filtered_sentences)
nouns = [word for word, pos in morphs if pos.startswith('N')]
verbs = [word for word, pos in morphs if pos.startswith('V')]
nouns = filter_words(nouns)
verbs = filter_words(verbs)
print("명사:", nouns)
print("동사:", verbs)


#4.14 최종수정부
# konlpy와 세그먼트 추출 결합방식, 이후 konlpy부분에서 동사랑 명사 추출 그리고 걸리는 시간 고려해 변경예정
#분리된 것들을 위키Api로도 분석하도록 함. 그전에 konlpy를 이용해 정확성 올림
# 모든 것들 다 결합한 버젼
#위 테스트 코드를 다 포함하고있음.
from konlpy.tag import Okt
import pandas as pd
from youtube_transcript_api import YouTubeTranscriptApi
import urllib.parse
import urllib.request
import json

class KoreanScriptExtractor:
    def __init__(self, vid, setTime, NUM_OF_WORDS=5):
        self.vid = vid
        self.scriptData = []
        self.setTime = setTime
        self.NUM_OF_WORDS = NUM_OF_WORDS

    # 유튜브 스크립트 추출
    def extract(self):
        # YouTube 비디오 ID 가져오기
        video_id = self.vid.split("v=")[1]

        # YouTube 자막 가져오기
        transcript = YouTubeTranscriptApi.get_transcript(video_id)

        # 자막 텍스트 추출
        segments = [segment['text'] for segment in transcript]

        self.scriptData = segments

    # Konlpy를 사용하여 형태소 분석 및 품사 태깅
    def konlpy_analysis(self):
        okt = Okt()  # Konlpy의 Okt 형태소 분석기 인스턴스 생성

        for segment in self.scriptData:
            analyzed_segment = okt.pos(segment)
            nouns = [word for word, pos in analyzed_segment if pos.startswith('N')]
            filtered_nouns = [self.remove_stopwords(word) for word in nouns]
            print("Segment Nouns (after removing stopwords):", filtered_nouns)

    # 불용어 제거
    def remove_stopwords(self, text):
        with open('stopwords-ko.txt', 'r', encoding='utf-8') as file:
            stopwords = set(line.strip() for line in file)
        return " ".join(word for word in text.split() if word not in stopwords)

    # Wikifier API를 사용하여 개념 추출
    def call_wikifier(self, text, lang="en", threshold=0.8, numberOfKCs=10):
        # Prepare the URL.
        data = urllib.parse.urlencode([
                ("text", text), ("lang", lang),
                ("userKey", self.wikiUserKey),
                ("pageRankSqThreshold", "%g" % threshold),
                ("applyPageRankSqThreshold", "true"),
                ("nTopDfValuesToIgnore", "200"),
                ("nWordsToIgnoreFromList", "200"),
                ("wikiDataClasses", "false"),
                ("wikiDataClassIds", "false"),
                ("support", "false"),
                ("ranges", "false"),
                ("minLinkFrequency", "3"),
                ("includeCosines", "false"),
                ("maxMentionEntropy", "2")
                ])
        url = "http://www.wikifier.org/annotate-article"

        # Call the Wikifier and read the response.
        req = urllib.request.Request(url, data=data.encode("utf8"), method="POST")
        with urllib.request.urlopen(req, timeout=60) as f:
            response = f.read()
            response = json.loads(response.decode("utf8"))

        sorted_data = sorted(response['annotations'], key=lambda x: x['pageRank'], reverse=True)
        # Output the annotations.
        num = 0
        result = []
        for annotation in sorted_data:
            if num < numberOfKCs:
                result.append({"title":annotation["title"],"url":annotation["url"],"pageRank":annotation["pageRank"]})
            num += 1
        return result

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

if __name__ == "__main__":
    extractor = KoreanScriptExtractor(vid="유튜브 영상 ID", setTime=600)
    wiki_data = extractor.url_to_wiki()
    print(wiki_data)
