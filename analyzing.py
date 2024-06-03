import pandas as pd

# 데이터 로드 (예: CSV 파일)
data = pd.read_csv('rs1.csv')
# 동사만 이용한다.
verbs = data[data['pos'] == 'verb']
# 시작시간과 종료시간을 이용하여 구간을 나눔
verbs['segment'] = data.apply(lambda row: f"{int(row['start_time'] // 60) * 60}-{int(row['end_time'] // 60) * 60}", axis=1)
print(verbs.groupby('segment').size())

# 구간별 동사 빈도 계산
verb_counts = verbs.groupby(['url', 'segment', 'word']).size().reset_index(name='count')
print(verb_counts)

def load_dictionary(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file]

# 각 단계별 사전 로드
remember = load_dictionary('remembering.txt')
understand = load_dictionary('understanding.txt')
apply = load_dictionary('applying.txt')
analyze = load_dictionary('analyzing.txt')
evaluate = load_dictionary('evaluating.txt')
create = load_dictionary('creating.txt')

bloom_dict = {
    'remember': remember,
    'understand': understand,
    'apply': apply,
    'analyze': analyze,
    'evaluate': evaluate,
    'create': create
}

def tag_bloom_stage(word, bloom_dict):
    for stage, words in bloom_dict.items():
        if word in words:
            return stage
    return 'unknown'

verb_counts['bloom_stage'] = verb_counts['word'].apply(lambda word: tag_bloom_stage(word, bloom_dict))

unknown_verbs = verb_counts[verb_counts['bloom_stage'] == 'unknown']
unknown_verbs.to_csv('unknown_verbs.csv')
print(unknown_verbs)

bloom_distribution = verb_counts.groupby(['segment', 'bloom_stage']).size().unstack(fill_value=0)
print(bloom_distribution)