from konlpy.tag import Kkma
import pandas as pd

# 텍스트 데이터 정의
text_ = "안녕하세요. 한국어 자연어 처리 테스트입니다."

# 문장 분리
kkma = Kkma()
text_sentences = kkma.sentences(text_)

# 종결 단어 리스트
lst = ['죠', '다', '요', '시오', '습니까', '십니까', '됩니까', '옵니까', '뭡니까', '합니다']

# 비동사 목록 불러오기
df = pd.read_csv('not_verb.csv', encoding='utf-8')
not_verb = df.stop.tolist()

# 단어 단위로 분리하여 리스트로 저장
text_all = ' '.join(text_sentences).split(' ')

for n in range(len(text_all)):
    i = text_all[n]
    if len(i) == 1:
        continue
    else:
        for j in lst:
            if j in i:
                if j in ['합니다']:
                    i += '!'
                else:
                    i += '?'
                break
        else:
            if i not in not_verb:
                continue
            else :
                if j == i[len(i)-1] :
                    text_all[n] += '.'
                    print(text_all[n], end='/')
