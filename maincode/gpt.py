import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from sklearn.feature_extraction.text import TfidfVectorizer
import openai
import re

class BloomAnalysisWithGPTandDictionary:
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
        # 언어 감지
        if re.search('[\u3131-\uD79D]', word):
            return 'Korean'
        elif re.search('[a-zA-Z]', word):
            return 'English'
        return 'Other'

    def process_verbs(self):
        self.data['language'] = self.data['word'].apply(self.detect_language)
        verbs = self.data[self.data['pos'] == 'verb'].copy()
        verbs['segment'] = verbs.apply(lambda row: int(row['start_time'] // 60) * 60, axis=1)
        self.verb_counts = verbs.groupby(['segment', 'word', 'language']).size().reset_index(name='count')
        self.verb_counts['bloom_stage'] = self.verb_counts.apply(
            lambda row: self.compare_bloom_stage(row['word'], row['language'], row['text']), axis=1
        )

    def tag_bloom_stage(self, word, language):
        # 사전 기반 단어 분석
        bloom_dict = self.bloom_dict_ko if language == 'Korean' else self.bloom_dict_en
        for stage, words in bloom_dict.items():
            if word in words:
                return stage
        return 'unknown'

    def gpt_bloom_classification(self, text):
        # GPT 기반 문장 분석
        prompt = f"Classify the following text into Bloom's Taxonomy stages: {text}"
        response = openai.Completion.create(
            engine="gpt-3.5-turbo",
            prompt=prompt,
            max_tokens=50,
            temperature=0.7
        )
        return response.choices[0].text.strip()

    def compare_bloom_stage(self, word, language, sentence):
        # 단어 기반 결과
        word_based_stage = self.tag_bloom_stage(word, language)
        
        # GPT 기반 결과
        sentence_based_stage = self.gpt_bloom_classification(sentence)
        
        # 두 결과를 우선순위에 따라 비교
        if word_based_stage == 'unknown':
            return sentence_based_stage
        elif sentence_based_stage == 'unknown':
            return word_based_stage
        else:
            # 우선순위가 높은 단계 선택
            return self.choose_better_stage(word_based_stage, sentence_based_stage)

    def choose_better_stage(self, word_stage, sentence_stage):
        # Bloom 단계 우선순위에 따른 비교
        if self.bloom_priority[word_stage] < self.bloom_priority[sentence_stage]:
            return word_stage
        else:
            return sentence_stage

    def calculate_bloom_distribution(self):
        # 구간별 Bloom 단계 분포 계산
        self.bloom_distribution = self.verb_counts.groupby(['segment', 'bloom_stage']).size().unstack(fill_value=0)
        self.bloom_distribution['decided_stage'] = self.bloom_distribution.apply(self.decide_bloom_stage, axis=1)

    def decide_bloom_stage(self, row):
        # 각 구간에서 우세한 단계 결정
        stages = row.drop('unknown').to_dict()
        if not stages:
            return 'unknown'
        return max(stages, key=lambda stage: (stages[stage], -self.bloom_priority[stage]))

    def merge_segments(self):
        # 연속된 동일 단계 구간 병합
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
        # Bloom 단계별 도넛 차트
        bloom_counts = self.verb_counts['bloom_stage'].value_counts().reset_index()
        bloom_counts.columns = ['bloom_stage', 'counts']
        bloom_counts = bloom_counts[bloom_counts['bloom_stage'] != 'unknown']

        color_map = {
            'remember': '#8290c4',     
            'understand': '#88c1e8',   
            'apply': '#74ac80',        
            'analyze': '#b1d984',      
            'evaluate': '#fae373',     
            'create': '#fb8976'        
        }

        fig = px.pie(bloom_counts, names='bloom_stage', values='counts', hole=0.5,
                     color='bloom_stage',  
                     color_discrete_map=color_map)
        fig.show()

    def plot_dot_graph(self, merged_segments):
        # Bloom 단계별 시간 흐름 그래프
        bloom_stage_mapping = {
            'remember': 1,
            'understand': 2,
            'apply': 3,
            'analyze': 4,
            'evaluate': 5,
            'create': 6
        }
        color_map = {
            'remember': '#8290c4',
            'understand': '#88c1e8',
            'apply': '#74ac80',
            'analyze': '#b1d984',
            'evaluate': '#fae373',
            'create': '#fb8976'
        }

        final_result = pd.DataFrame(merged_segments, columns=['start_segment', 'end_segment', 'bloom_stage'])
        final_result['bloom_stage_numeric'] = final_result['bloom_stage'].map(bloom_stage_mapping)
        final_result['bloom_color'] = final_result['bloom_stage'].map(color_map)

        dot_trace = go.Scatter(
            x=final_result['start_segment'],  
            y=final_result['bloom_stage_numeric'],  
            mode='markers+lines',  
            marker=dict(
                size=10,
                color=final_result['bloom_color']  
            ),
            line=dict(
                width=2,
                color='gray'  
            ),  
            name='Bloom Stages'
        )

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
        # 각 Bloom 단계의 시작-종료 시간 구간 포맷팅
        stage_dict = {}
        for segment in merged_segments:
            start_time, end_time, stage = segment
            if stage not in stage_dict:
                stage_dict[stage] = []
            stage_dict[stage].append(f"{start_time}-{end_time}")
        stage_segments = {stage: ', '.join(segments) for stage, segments in stage_dict.items()}
        return stage_segments

    def analyze_nouns(self, top_n=5):
        # 명사 분석 및 상위 N개 명사 추출
        nouns = self.data[self.data['pos'] == 'noun']
        nouns_text = ' '.join(nouns['word'])
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([nouns_text])

        feature_names = vectorizer.get_feature_names()
        tfidf_scores = tfidf_matrix.toarray()[0]
        top_n_indices = tfidf_scores.argsort()[-top_n:][::-1]
        return [feature_names[i] for i in top_n_indices]

    @staticmethod
    def load_dictionary(file_path):
        # 사전 로드
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file]

# 한국어 및 영어 단계별 Bloom 사전 로드
bloom_dict_ko = {
    'remember': BloomAnalysisWithGPTandDictionary.load_dictionary('KR_bloom_dictionary/remembering.txt'),
    'understand': BloomAnalysisWithGPTandDictionary.load_dictionary('KR_bloom_dictionary/understanding.txt'),
    'apply': BloomAnalysisWithGPTandDictionary.load_dictionary('KR_bloom_dictionary/applying.txt'),
    'analyze': BloomAnalysisWithGPTandDictionary.load_dictionary('KR_bloom_dictionary/analyzing.txt'),
    'evaluate': BloomAnalysisWithGPTandDictionary.load_dictionary('KR_bloom_dictionary/evaluating.txt'),
    'create': BloomAnalysisWithGPTandDictionary.load_dictionary('KR_bloom_dictionary/creating.txt')
}

bloom_dict_en = {
    'remember': BloomAnalysisWithGPTandDictionary.load_dictionary('EN_bloom_dictionary/remembering.txt'),
    'understand': BloomAnalysisWithGPTandDictionary.load_dictionary('EN_bloom_dictionary/understanding.txt'),
    'apply': BloomAnalysisWithGPTandDictionary.load_dictionary('EN_bloom_dictionary/applying.txt'),
    'analyze': BloomAnalysisWithGPTandDictionary.load_dictionary('EN_bloom_dictionary/analyzing.txt'),
    'evaluate': BloomAnalysisWithGPTandDictionary.load_dictionary('EN_bloom_dictionary/evaluating.txt'),
    'create': BloomAnalysisWithGPTandDictionary.load_dictionary('EN_bloom_dictionary/creating.txt')
}

# 사용 예시
bloom_analysis = BloomAnalysisWithGPTandDictionary('new.csv', bloom_dict_ko, bloom_dict_en)
bloom_analysis.process_verbs()
bloom_analysis.calculate_bloom_distribution()
merged_segments = bloom_analysis.merge_segments()

# 그래프 출력
bloom_analysis.plot_donut_chart()
bloom_analysis.plot_dot_graph(merged_segments)

# 각 단계별 구간 출력
stage_segments = bloom_analysis.format_stage_segments(merged_segments)

for stage, segments in stage_segments.items():
    print(f"{stage}: {segments}")