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
