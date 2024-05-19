from konlpy.tag import Kkma
import pandas as pd
from youtube_transcript_api import YouTubeTranscriptApi

# YouTube 비디오 ID
video_id = "s8l6r4-P__k"

# YouTube 자막 가져오기
srt = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])

# 자막 텍스트 추출
text_ = ""
for i in srt:
    text_ += i['text'] + " "

# 문장 분리
kkma = Kkma()
text_sentences = kkma.sentences(text_)

# 종결 단어 리스트
lst = ['죠', '다', '요', '시오', '습니까', '십니까', '됩니까', '옵니까', '뭡니까']

# 비동사 목록 불러오기
df = pd.read_csv('not_verb.csv', encoding='utf-8')
not_verb = df.stop.tolist()

# 단어 단위로 분리하여 리스트로 저장
text_all = [char for sentence in text_sentences for char in sentence]

# 문장에 구두점 추가
for n in range(len(text_all)):
    i = text_all[n]
    if len(i) == 1:
        continue
    else:
        for j in lst:
            if j in i:
                if j in ['시오', '됩니까']:
                    i += '!'
                else:
                    i += '?'
                break
        else:
            if i not in not_verb:
                if i[-1] in lst:
                    i += '.'

    text_all[n] = i

# 수정된 문장 출력
for sentence in text_sentences:
    print(''.join(text_all[:len(sentence)]), end='/')
    text_all = text_all[len(sentence):]
