import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import re
import plotly.express as px
import plotly.graph_objects as go
7869
class BloomAnalysis:
    def __init__(self, data_path, bloom_dict_ko, bloom_dict_en):
        self.data = pd.read_csv(data_path)
        self.bloom_dict_ko = bloom_dict_ko
        self.bloom_dict_en = bloom_dict_en
        self.bloom_priority = {
            'remember': 6,
            'understand': 5,
            'apply': 4,
            'analyze': 3,
            'evaluate': 2,
            'create': 1
        }

    def detect_language(self, word):
        if re.search('[\u3131-\uD79D]', word):
            return 'Korean'
        elif re.search('[a-zA-Z]', word):
            return 'English'
        return 'Other'

    def process_verbs(self):
        self.data['language'] = self.data['word'].apply(self.detect_language)
        verbs = self.data[self.data['pos'] == 'verb'].copy()  # 복사본 생성
        verbs['segment'] = verbs.apply(lambda row: int(row['start_time'] // 60) * 60, axis=1)
        self.verb_counts = verbs.groupby(['segment', 'word', 'language']).size().reset_index(name='count')
        self.verb_counts['bloom_stage'] = self.verb_counts.apply(lambda row: self.tag_bloom_stage(row['word'], row['language']), axis=1)

    def tag_bloom_stage(self, word, language):
        bloom_dict = self.bloom_dict_ko if language == 'Korean' else self.bloom_dict_en
        for stage, words in bloom_dict.items():
            if word in words:
                return stage
        return 'unknown'

    def calculate_bloom_distribution(self):
        self.bloom_distribution = self.verb_counts.groupby(['segment', 'bloom_stage']).size().unstack(fill_value=0)
        self.bloom_distribution['decided_stage'] = self.bloom_distribution.apply(self.decide_bloom_stage, axis=1)

    def decide_bloom_stage(self, row):
        stages = row.drop('unknown').to_dict()
        if not stages:
            return 'unknown'
        return max(stages, key=lambda stage: (stages[stage], -self.bloom_priority[stage]))

    def merge_segments(self):
        merged_segments = []
        start_segment, prev_stage = None, None
    
        for segment, row in self.bloom_distribution.iterrows():
            stage = row['decided_stage']
            if stage != prev_stage:
                if prev_stage is not None:
                    merged_segments.append((start_segment, segment, prev_stage))
                start_segment = segment
            prev_stage = stage
    
        if prev_stage is not None:
            merged_segments.append((start_segment, segment + 60, prev_stage))

        return merged_segments

    def plot_donut_chart(self):
        bloom_counts = self.verb_counts['bloom_stage'].value_counts().reset_index()
        bloom_counts.columns = ['bloom_stage', 'counts']
        bloom_counts = bloom_counts[bloom_counts['bloom_stage'] != 'unknown']

        # 이미지에서 색상 추출한 색상 맵핑 설정
        color_map = {
            'remember': '#8290c4',     # 진한 파랑
            'understand': '#88c1e8',   # 밝은 파랑
            'apply': '#74ac80',        # 초록
            'analyze': '#b1d984',      # 연두
            'evaluate': '#fae373',     # 노랑
            'create': '#fb8976'        # 빨강
        }

        fig = px.pie(bloom_counts, names='bloom_stage', values='counts', hole=0.5,
                     color='bloom_stage',  # 컬러 맵 적용
                     color_discrete_map=color_map)
        fig.show()

    def plot_dot_graph(self, merged_segments):
        bloom_stage_mapping = {
            'remember': 1,
            'understand': 2,
            'apply': 3,
            'analyze': 4,
            'evaluate': 5,
            'create': 6
        }
        # 이미지에서 색상 추출한 색상 맵핑 설정
        color_map = {
            'remember': '#8290c4',     # 진한 파랑
            'understand': '#88c1e8',   # 밝은 파랑
            'apply': '#74ac80',        # 초록
            'analyze': '#b1d984',      # 연두
            'evaluate': '#fae373',     # 노랑
            'create': '#fb8976'        # 빨강
        }

        final_result = pd.DataFrame(merged_segments, columns=['start_segment', 'end_segment', 'bloom_stage'])
        final_result['bloom_stage_numeric'] = final_result['bloom_stage'].map(bloom_stage_mapping)
        final_result['bloom_color'] = final_result['bloom_stage'].map(color_map)  # 각 단계에 맞는 색상 매핑

         # 도트 그래프 생성
        dot_trace = go.Scatter(
            x=final_result['start_segment'],  
            y=final_result['bloom_stage_numeric'],  
            mode='markers+lines',  
            marker=dict(
                size=10,
                color=final_result['bloom_color']  # 단계별 색상 적용
            ),
            line=dict(
                width=2,
                color='gray'  # 선 색상 설정 (단계와 다른 색상)
            ),  
            name='Bloom Stages'
        )

          # 레이아웃 설정
        layout = go.Layout(
            title='Bloom Stages Over Time',
            xaxis_title='Time (seconds)',
            yaxis_title='Bloom Stage (numeric)',
            yaxis=dict(
                tickvals=[1, 2, 3, 4, 5, 6], 
                ticktext=['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']
            ),
            showlegend=False
        )
        fig = go.Figure(data=[dot_trace], layout=layout)
        fig.show()

    def format_stage_segments(self, merged_segments):
        stage_dict = {}
        for segment in merged_segments:
            start_time, end_time, stage = segment
            if stage not in stage_dict:
                stage_dict[stage] = []
            stage_dict[stage].append(f"{start_time}-{end_time}")
        stage_segments = {stage: ', '.join(segments) for stage, segments in stage_dict.items()}
        return stage_segments

    def analyze_nouns(self, top_n=5):
        nouns = self.data[self.data['pos'] == 'noun']
        nouns_text = ' '.join(nouns['word'])
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([nouns_text])

        # get_feature_names() 메서드로 수정 (구버전 scikit-learn 지원)
        feature_names = vectorizer.get_feature_names()  # get_feature_names_out() 대신 사용
        tfidf_scores = tfidf_matrix.toarray()[0]
        top_n_indices = tfidf_scores.argsort()[-top_n:][::-1]
        return [feature_names[i] for i in top_n_indices]
    
    @staticmethod
    def load_dictionary(file_path):
        # CSV 사전 파일 로드
        dictionary_data = pd.read_csv(file_path)
        return dictionary_data['words'].tolist() 

# 한국어 및 영어 단계별 사전 로드
bloom_dict_ko = {
    'remember': BloomAnalysis.load_dictionary('KR_bloom_dictionary/remembering.csv'),
    'understand': BloomAnalysis.load_dictionary('KR_bloom_dictionary/understanding.csv'),
    'apply': BloomAnalysis.load_dictionary('KR_bloom_dictionary/applying.csv'),
    'analyze': BloomAnalysis.load_dictionary('KR_bloom_dictionary/analyzing.csv'),
    'evaluate': BloomAnalysis.load_dictionary('KR_bloom_dictionary/evaluating.csv'),
    'create': BloomAnalysis.load_dictionary('KR_bloom_dictionary/creating.csv')
}

bloom_dict_en = {
    'remember': BloomAnalysis.load_dictionary('EN_bloom_dictionary/remembering.csv'),
    'understand': BloomAnalysis.load_dictionary('EN_bloom_dictionary/understanding.csv'),
    'apply': BloomAnalysis.load_dictionary('EN_bloom_dictionary/applying.csv'),
    'analyze': BloomAnalysis.load_dictionary('EN_bloom_dictionary/analyzing.csv'),
    'evaluate': BloomAnalysis.load_dictionary('EN_bloom_dictionary/evaluating.csv'),
    'create': BloomAnalysis.load_dictionary('EN_bloom_dictionary/creating.csv')
}

# 클래스 사용 예시
bloom_analysis = BloomAnalysis('new.csv', bloom_dict_ko, bloom_dict_en)
bloom_analysis.process_verbs()
bloom_analysis.calculate_bloom_distribution()
merged_segments = bloom_analysis.merge_segments()

# 그래프 출력
bloom_analysis.plot_donut_chart()
bloom_analysis.plot_dot_graph(merged_segments)

# 각 단계별 구간 표시
stage_segments = bloom_analysis.format_stage_segments(merged_segments)

# 결과 출력
for stage, segments in stage_segments.items():
    print(f"{stage}: {segments}")

# 명사 상위 5개 출력
top_n_nouns = bloom_analysis.analyze_nouns()
print("TF-IDF 분석 결과:", top_n_nouns)