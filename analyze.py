import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 사전 파일 경로
dictionary_paths = {
    'remember': 'remembering.txt',
    'understand': 'understanding.txt',
    'apply': 'applying.txt',
    'analyze': 'analyzing.txt',
    'evaluate': ' evaluating.txt',
    'create': 'creating.txt'
}

# 사전 로드
dictionaries = {}
for stage, path in dictionary_paths.items():
    with open(path, 'r', encoding='utf-8') as file:
        dictionaries[stage] = file.read().splitlines()

# 단어 백터화
# 자막 데이터 로드
#학습 및 테스트 데이터 셋 분리
#모델 학습
#모델 평가
#자막데이터 예측

