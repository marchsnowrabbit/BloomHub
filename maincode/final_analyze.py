# 영어 사전 출처: Bloom's Taxonomy of Measurable Verbs Utica University
#https://www.utica.edu › Blooms Taxonomy - Best
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import re
import seaborn as sns
import plotly.express as px #그래프웹 api
import plotly.graph_objects as go

# 데이터 로드 (예: CSV 파일)
data = pd.read_csv('new.csv')

# 언어를 감지하는 함수
def detect_language(word):
    if re.search('[\u3131-\uD79D]', word):  # 한글 유니코드 범위
        return 'Korean'
    elif re.search('[a-zA-Z]', word):  # 영어 알파벳
        return 'English'
    else:
        return 'Other'

# 언어 감지 결과를 데이터에 추가
data['language'] = data['word'].apply(detect_language)

# 동사만 이용
verbs = data[data['pos'] == 'verb']

# 시작시간과 종료시간을 이용하여 구간을 나눔
verbs['segment'] = verbs.apply(lambda row: f"{int(row['start_time'] // 60) * 60}-{int(row['end_time'] // 60) * 60}", axis=1)

# 구간을 숫자형으로 변환하여 정렬
verbs['segment'] = verbs['segment'].str.split('-').apply(lambda x: int(x[0]))

# 구간별 동사 빈도 계산
verb_counts = verbs.groupby(['segment', 'word', 'language']).size().reset_index(name='count')

# 각 단계별 사전 로드 함수
def load_dictionary(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file]

# 한국어 및 영어 단계별 사전 로드
bloom_dict_ko = {
    'remember': load_dictionary('KR_bloom_dictionary/remembering.txt'),
    'understand': load_dictionary('KR_bloom_dictionary/understanding.txt'),
    'apply': load_dictionary('KR_bloom_dictionary/applying.txt'),
    'analyze': load_dictionary('KR_bloom_dictionary/analyzing.txt'),
    'evaluate': load_dictionary('KR_bloom_dictionary/evaluating.txt'),
    'create': load_dictionary('KR_bloom_dictionary/creating.txt')
}

bloom_dict_en = {
    'remember': load_dictionary('EN_bloom_dictionary/remembering.txt'),
    'understand': load_dictionary('EN_bloom_dictionary/understanding.txt'),
    'apply': load_dictionary('EN_bloom_dictionary/applying.txt'),
    'analyze': load_dictionary('EN_bloom_dictionary/analyzing.txt'),
    'evaluate': load_dictionary('EN_bloom_dictionary/evaluating.txt'),
    'create': load_dictionary('EN_bloom_dictionary/creating.txt')
}

bloom_priority = {
    'remember': 6,
    'understand': 5,
    'apply': 4,
    'analyze': 3,
    'evaluate': 2,
    'create': 1
}

# Bloom 단계 태깅 함수
def tag_bloom_stage(word, language):
    bloom_dict = bloom_dict_ko if language == 'Korean' else bloom_dict_en
    for stage, words in bloom_dict.items():
        if word in words:
            return stage
    return 'unknown'

verb_counts['bloom_stage'] = verb_counts.apply(lambda row: tag_bloom_stage(row['word'], row['language']), axis=1)

############################################분석되지 않은 부분
# # unknown 단어 파악하기
# unknown_verbs = verb_counts[verb_counts['bloom_stage'] == 'unknown']
# unknown_verbs.to_csv('unknown_verbs.csv', index=False)
################################################################

# 구간별 Bloom 단계 빈도 계산
bloom_distribution = verb_counts.groupby(['segment', 'bloom_stage']).size().unstack(fill_value=0)
print("상세 비교:")
print(bloom_distribution) 

# 구간별 Bloom 단계 결정
def decide_bloom_stage(row):
    stages = row.drop('unknown').to_dict()
    if not stages:
        return 'unknown'
    max_count = max(stages.values())
    most_frequent_stages = [stage for stage, count in stages.items() if count == max_count]
    if len(most_frequent_stages) == 1:
        return most_frequent_stages[0]
    else:
        # 동일한 빈도의 단계가 여러 개 있을 경우, 가장 낮은 단계로 매핑
        return sorted(most_frequent_stages, key=lambda stage: bloom_priority[stage], reverse=True)[0]

bloom_distribution['decided_stage'] = bloom_distribution.apply(decide_bloom_stage, axis=1)
print(bloom_distribution)

# 구간 합치기
def merge_segments(bloom_distribution):
    merged_segments = []
    start_segment = None
    prev_stage = None
    prev_end_time = None

    for segment, row in bloom_distribution.iterrows():
        stage = row['decided_stage']

        start_time = segment 
        end_time = segment + 60

        if prev_stage != stage:
            if prev_stage is not None:
                merged_segments.append((start_segment, prev_end_time, prev_stage))
            start_segment = start_time
            prev_stage = stage
            prev_end_time = end_time
        else:
            # 인접한 구간의 Bloom 단계가 같으면 계속해서 병합
            prev_end_time = end_time

    # 마지막 구간 처리
    if prev_stage is not None:
        merged_segments.append((start_segment, prev_end_time, prev_stage))

    return merged_segments

merged_segments = merge_segments(bloom_distribution)

# 전체 영상의 Bloom 태그 결정
overall_bloom_stage = verb_counts[verb_counts['bloom_stage'] != 'unknown']['bloom_stage'].value_counts().idxmin()

# 결과 저장
final_result = pd.DataFrame(merged_segments, columns=['start_segment', 'end_segment', 'bloom_stage'])
final_result['overall_bloom_stage'] = overall_bloom_stage
print("구간별 bloom 단계:")
print(final_result) #최종결과

###################################################################
#도넛 그래프(전체 퍼센트)
import plotly.express as px

# 전체 Bloom 단계 비율 계산
bloom_counts = verb_counts['bloom_stage'].value_counts().reset_index()
bloom_counts.columns = ['bloom_stage', 'counts']  # 열 이름을 'counts'로 설정

# 'unknown' 단계 제외
bloom_counts = bloom_counts[bloom_counts['bloom_stage'] != 'unknown']

# 도넛 차트 그리기
fig = px.pie(bloom_counts, names='bloom_stage', values='counts', hole=0.5)
fig.show()
##########################################################################
# 선으로 연결된 도트 그래프
bloom_stage_mapping = {
    'remember': 1,
    'understand': 2,
    'apply': 3,
    'analyze': 4,
    'evaluate': 5,
    'create': 6
}

# 단계 값을 숫자로 변환
final_result['bloom_stage_numeric'] = final_result['bloom_stage'].map(bloom_stage_mapping)

# 선으로 연결된 도트 그래프 (숫자 값)
dot_trace = go.Scatter(
    x=final_result['start_segment'],  # 시작 구간
    y=final_result['bloom_stage_numeric'],  # Bloom 단계 숫자
    mode='markers+lines',  # 점과 선
    marker=dict(size=10),  # 점 크기
    line=dict(width=2),  # 선 두께
    name='Bloom Stages'
)

layout = go.Layout(
    title='Bloom Stages Over Time',
    xaxis_title='Time (seconds)',
    yaxis_title='Bloom Stage (numeric)',
    yaxis=dict(tickvals=[1, 2, 3, 4, 5, 6], ticktext=['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']),
    showlegend=True
)

fig = go.Figure(data=[dot_trace], layout=layout)
fig.show()
######################################################################

# 명사 분석
nouns = data[data['pos'] == 'noun']
nouns_text = ' '.join(nouns['word'])
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform([nouns_text])
feature_names = vectorizer.get_feature_names()
tfidf_scores = tfidf_matrix.toarray()[0]

# TF-IDF 점수를 기준으로 상위 단어 선택
top_n = 5
top_n_indices = tfidf_scores.argsort()[-top_n:][::-1]
top_n_words = [feature_names[i] for i in top_n_indices]

# 결과 출력
print("TF-IDF 분석 결과:", top_n_words)