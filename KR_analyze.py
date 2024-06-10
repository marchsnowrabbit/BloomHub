import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter

# 데이터 로드 (예: CSV 파일)
data = pd.read_csv('reduce1.csv')

# 동사만 이용한다.
verbs = data[data['pos'] == 'verb']

# 시작시간과 종료시간을 이용하여 구간을 나눔
verbs['segment'] = verbs.apply(lambda row: f"{int(row['start_time'] // 60) * 60}-{int(row['end_time'] // 60) * 60}", axis=1)

# 구간을 숫자형으로 변환하여 정렬
verbs['segment'] = verbs['segment'].str.split('-').apply(lambda x: int(x[0]))

# 구간별 동사 빈도 계산
verb_counts = verbs.groupby(['segment', 'word']).size().reset_index(name='count')
def load_dictionary(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file]

# 각 단계별 사전 로드
remember = load_dictionary('KR_bloom_dictionary/remembering.txt')
understand = load_dictionary('KR_bloom_dictionary/understanding.txt')
apply = load_dictionary('KR_bloom_dictionary/applying.txt')
analyze = load_dictionary('KR_bloom_dictionary/analyzing.txt')
evaluate = load_dictionary('KR_bloom_dictionary/evaluating.txt')
create = load_dictionary('KR_bloom_dictionary/creating.txt')

bloom_dict = {
    'remember': remember,
    'understand': understand,
    'apply': apply,
    'analyze': analyze,
    'evaluate': evaluate,
    'create': create
}

bloom_priority = {
    'remember': 6,
    'understand': 5,
    'apply': 4,
    'analyze': 3,
    'evaluate': 2,
    'create': 1
}

def tag_bloom_stage(word, bloom_dict):
    for stage, words in bloom_dict.items():
        if word in words:
            return stage
    return 'unknown'

verb_counts['bloom_stage'] = verb_counts['word'].apply(lambda word: tag_bloom_stage(word, bloom_dict))

# unknown 단어 파악하기
unknown_verbs = verb_counts[verb_counts['bloom_stage'] == 'unknown']
unknown_verbs.to_csv('unknown_verbs.csv', index=False)

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
        return sorted(most_frequent_stages, key=lambda stage: bloom_priority[stage])[0]

bloom_distribution['decided_stage'] = bloom_distribution.apply(decide_bloom_stage, axis=1)
print(bloom_distribution)
##########구간 합치기 ###########################

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

# 결과 저장
final_result = pd.DataFrame(merged_segments, columns=['start_segment', 'end_segment', 'bloom_stage'])
print("구간별 bloom 단계:")
print(final_result)
# final_result.to_csv('final_bloom_stages.csv', index=False)


########태그###########################

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
