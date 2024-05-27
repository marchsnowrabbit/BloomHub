#고려해야 하는 것들
# 뽑아낸 script_extractor의 데이터를 생각해보자
#1. 제목, url,페이지랭크,단어명,시작시간,종료시간 형태의 데이터
#1-1. 시작시간과 종료시간은 0 , 60 / 60, 120 이런식으로 나누어져 있다.
#1-2. 구간별로 bloom 분석기로 자동 태깅 예정
#2. 구간별로 분석하는게 목표, 좀더 정리하기 위해서 wordcount를 이용해서 단어 반복횟수 분석
#3. 기계학습을 어떻게 시킬 것인가? 
#3.1 - 구조 예상
# 단어 -> bloom분석기(가제)-> 단계를 알려줌) : 기본베이스
# 구간의 단어들 -> bloom분석기(가제)-> 각 구간별 단계를 알려줌(최종형태)
#(영상링크,구간,bloom단계) 이런식으로 나와야 함
# 대충 예제로는 이런 형태 (video url1,0-60,remember),(vidio url2,120-180,apply)
# 같은 영상속 다른 구간이어도 이어지는 구간이면 같은 bloom 단게라면 통합한다
# 이렇게 (video url1,0-60,remember)(video url1,60-120,remember)-> (videourl1,0-120,remember)
#3.2 bloom분석기가 수행해야 할 기능
# 단어의 중복횟수,구간의 단어 bloom단계별 유사도 비교후 가장 높은 것으로 각 구간별 bloom인지 단계의 태깅.

import pandas as pd

# 각 단계별 사전 로드
def load_dictionary(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file]

knowledge_words = load_dictionary('knowledge.txt')
comprehension_words = load_dictionary('comprehension.txt')
application_words = load_dictionary('application.txt')
analysis_words = load_dictionary('analysis.txt')
synthesis_words = load_dictionary('synthesis.txt')
evaluation_words = load_dictionary('evaluation.txt')

# 사전을 단계별로 저장
bloom_dict = {
    'knowledge': knowledge_words,
    'comprehension': comprehension_words,
    'application': application_words,
    'analysis': analysis_words,
    'synthesis': synthesis_words,
    'evaluation': evaluation_words
}


# 단어 백터화
# 자막 데이터 로드
#학습 및 테스트 데이터 셋 분리
#모델 학습
#모델 평가
#자막데이터 예측

