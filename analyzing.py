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

#unkown단어 파악하기
unknown_verbs = verb_counts[verb_counts['bloom_stage'] == 'unknown']
unknown_verbs.to_csv('unknown_verbs.csv')
print(unknown_verbs)

#결과부
bloom_distribution = verb_counts.groupby(['segment', 'bloom_stage']).size().unstack(fill_value=0)
print(bloom_distribution)


#명사 자주나오는거 태그 5개 뽑기
nouns = data[data['pos'] == 'noun']
noun_counts = nouns['word'].value_counts().reset_index()
noun_counts.columns = ['word', 'count']
top_nouns = noun_counts.head(5)
print(top_nouns)

#추가예정 내용: 
#1.가장 많이 나온 태그 unkown제외하고가 같을 경우 어떻게 처리할까?
#2. bloom태그가 이어지는 구간일 경우 하나로 합쳐보이기
#(0-60)(60-120)이 apply일 경우 : (0-120)으로 표기
# 최종 부 ->  그래프로 태그 추론 이유 보여주기
# 단계를 숫자로 표기해 1 2 3 4 5 6으로한 후 구간별 그래프 보여주기
# 단계에 적절한 구간 보여주기!! -> 검색이나 filter로 구현