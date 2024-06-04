import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter

# 데이터 로드 (예: CSV 파일)
data = pd.read_csv('en.csv')
verbs = data[data['pos'] == 'verb']
# 시작시간과 종료시간을 이용하여 구간을 나눔
verbs['segment'] = data.apply(lambda row: f"{int(row['start_time'] // 60) * 60}-{int(row['end_time'] // 60) * 60}", axis=1)
print(verbs.groupby('segment').size())

# 구간별 동사 빈도 계산
verb_counts = verbs.groupby(['url', 'segment', 'word']).size().reset_index(name='count')
print(verb_counts)

nouns = data[data['pos'] == 'noun']
nouns_text = ' '.join(nouns['word'])
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform([nouns_text])
feature_names = vectorizer.get_feature_names()  # get_feature_names()로 수정
tfidf_scores = tfidf_matrix.toarray()[0]

# TF-IDF 점수를 기준으로 상위 단어 선택
top_n = 5
top_n_indices = tfidf_scores.argsort()[-top_n:][::-1]
top_n_words = [feature_names[i] for i in top_n_indices]
print("적절한 태그:", top_n_words)