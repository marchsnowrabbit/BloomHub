from konlpy.tag import Kkma 
import pandas as pd

kkma = Kkma()
text_ = "여기에 분석할 한국어 텍스트를 넣어주세요."  # 분석할 텍스트를 적절한 문자열로 대체해주세요.
text_sentences = kkma.sentences(text_)  # 문장 분리

# 종결 단어 리스트
lst = ['죠', '다', '요', '시오', '습니까', '십니까', '됩니까', '옵니까', '뭡니까']

# 불용어 리스트 불러오기
df = pd.read_csv('not_verb.csv', encoding='utf-8')
not_verb = df['stop'].tolist()

# 단어 단위로 분할된 텍스트를 저장할 리스트
text_all = []

# 단어 단위로 끊기
for sentence in text_sentences:
    words = sentence.split()
    for word in words:
        text_all.append(word)

# 종결 단어가 나오면 문장을 종결 기호로 바꿈
for n in range(len(text_all)):
    i = text_all[n]
    if len(i) == 1:
        continue
    else:
        for j in lst:
            if j in i:
                if j in lst[4]:  # '습니까' 등이면 물음표로 변경
                    i += '?'
                elif j == '시오':  # '시오'는 느낌표로 변경
                    i += '!'
                else:
                    if i in not_verb:
                        continue
                    else:
                        if j == i[len(i)-1]:
                            i += '.'  # 종결 단어면 마침표로 변경
                            text_all[n] = i  # 변경된 문장을 리스트에 반영
                            break

# 결과 출력
print(' '.join(text_all))
