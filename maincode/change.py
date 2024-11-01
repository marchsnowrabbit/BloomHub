import pandas as pd

# 텍스트 파일을 읽어 리스트로 변환
with open('KR_bloom_dictionary/stopwords-ko.txt', 'r', encoding='utf-8') as file:
    data = [line.strip() for line in file.readlines()]

# DataFrame으로 변환
df = pd.DataFrame(data, columns=['data'])

# CSV 파일로 저장
df.to_csv('KR_bloom_dictionary/stopwords-ko.csv', index=False, encoding='utf-8-sig')
