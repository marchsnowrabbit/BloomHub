import numpy as np
import pandas as pd
from transformers import BertTokenizer, BertForSequenceClassification, AutoTokenizer
import torch
import torch.nn.functional as F
import re
import plotly.express as px
import plotly.graph_objects as go

class BloomAnalysisWithBERTandKoBERT:
    def __init__(self, tag_data_path, bert_data_path, bloom_dict_ko, bloom_dict_en, kobert_model_path, bert_model_path):
        # 단어 태깅용 CSV 파일 불러오기
        self.tag_data = pd.read_csv(tag_data_path)
        
        # BERT 기반 문장 분석용 CSV 파일 불러오기
        self.bert_data = pd.read_csv(bert_data_path)
        
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
        # KoBERT 모델 및 토크나이저 로드
        self.kobert_tokenizer = AutoTokenizer.from_pretrained(kobert_model_path, trust_remote_code=True)  # KoBERT의 전용 토크나이저
        self.kobert_model = BertForSequenceClassification.from_pretrained(kobert_model_path, num_labels=6, trust_remote_code=True)
        self.kobert_model.eval()

        # BERT 모델 및 토크나이저 로드
        self.bert_tokenizer = AutoTokenizer.from_pretrained(bert_model_path)
        self.bert_model = BertForSequenceClassification.from_pretrained(bert_model_path, num_labels=6)
        self.bert_model.eval()

        # BERT 데이터 전처리
        self.process_bert_data()

    def detect_language(self, word):
        if re.search('[\u3131-\uD79D]', word):
            return 'Korean'
        elif re.search('[a-zA-Z]', word):
            return 'English'
        return 'Other'

    def process_verbs(self):
        # 태깅 데이터에서 언어를 감지하고 동사 추출
        self.tag_data['language'] = self.tag_data['word'].apply(self.detect_language)
        verbs = self.tag_data[self.tag_data['pos'] == 'verb'].copy()
        verbs['segment'] = verbs.apply(lambda row: int(row['start_time'] // 60) * 60, axis=1)
        self.verb_counts = verbs.groupby(['segment', 'word', 'language']).size().reset_index(name='count')
        print(self.verb_counts.columns)
        
        # 기존 태깅 방식 사용
        self.verb_counts['bloom_stage'] = self.verb_counts.apply(
            lambda row: self.tag_bloom_stage(row['word'], row['language']), axis=1)

        # BERT 또는 KoBERT 기반 예측 결합
        self.verb_counts['bert_bloom_stage'] = self.verb_counts.apply(
            lambda row: self.get_bert_bloom_stage(row['word'], row['language'], row['segment']), axis=1)

    def tag_bloom_stage(self, word, language):
        bloom_dict = self.bloom_dict_ko if language == 'Korean' else self.bloom_dict_en
        for stage, words in bloom_dict.items():
            if word in words:
                return stage
        return 'unknown'

    def get_bert_bloom_stage(self, word, language, segment):
        # 해당 segment에서 문장 구성 (문장 분석용 데이터에서 가져옴)
        sentence = self.get_sentence(segment)
        if language == 'Korean':
            # KoBERT를 사용한 문장 분석
            inputs = self.kobert_tokenizer(sentence, return_tensors="pt", truncation=True, padding=True)
            with torch.no_grad():
                outputs = self.kobert_model(**inputs)
        elif language == 'English':
            # BERT를 사용한 문장 분석
            inputs = self.bert_tokenizer(sentence, return_tensors="pt", truncation=True, padding=True)
            with torch.no_grad():
                outputs = self.bert_model(**inputs)
        else:
            return 'unknown'

        probs = F.softmax(outputs.logits, dim=-1)
        predicted_stage = torch.argmax(probs).item()

        # Bloom 단계 매핑
        bloom_stage_mapping = {
            0: 'remember',
            1: 'understand',
            2: 'apply',
            3: 'analyze',
            4: 'evaluate',
            5: 'create'
        }
        return bloom_stage_mapping[predicted_stage]
    
    def process_bert_data(self):
        # BERT 데이터에서 segment 추가
        if 'start_time' in self.bert_data.columns:
            self.bert_data['segment'] = self.bert_data.apply(lambda row: int(row['start_time'] // 60) * 60, axis=1)
        else:
            print("Error: 'start_time' column not found in bert_data.")
        
    def get_sentence(self, segment):
        # 문장 분석용 CSV 파일에서 주어진 segment에 해당하는 문장을 재구성
        if 'segment' in self.bert_data.columns:
            segment_data = self.bert_data[self.bert_data['segment'] == segment]
            sentence = ' '.join(segment_data['word'].values)
            return sentence
        else:
            print("Error: 'segment' column not found in bert_data.")
            return ""

    def calculate_bloom_distribution(self):
        self.bloom_distribution = self.verb_counts.groupby(['segment', 'bloom_stage', 'bert_bloom_stage']).size().unstack(fill_value=0)
        self.bloom_distribution['decided_stage'] = self.bloom_distribution.apply(self.decide_bloom_stage, axis=1)

    def decide_bloom_stage(self, row):
        stages = row.drop('unknown').to_dict()
        if not stages:
            return 'unknown'
        
        bert_stage = row['bert_bloom_stage']
        verb_stage = row['bloom_stage']
        
        if bert_stage == verb_stage:
            return verb_stage
        else:
            # 우선순위가 높은 단계로 선택
            return bert_stage if self.bloom_priority[bert_stage] < self.bloom_priority[verb_stage] else verb_stage

    def plot_donut_chart(self):
        bloom_counts = self.verb_counts['decided_stage'].value_counts().reset_index()
        bloom_counts.columns = ['bloom_stage', 'counts']
        bloom_counts = bloom_counts[bloom_counts['bloom_stage'] != 'unknown']

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


    @staticmethod
    def load_dictionary(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file]

# 한국어 및 영어 단계별 사전 로드
bloom_dict_ko = {
    'remember': BloomAnalysisWithBERTandKoBERT.load_dictionary('KR_bloom_dictionary/remembering.txt'),
    'understand': BloomAnalysisWithBERTandKoBERT.load_dictionary('KR_bloom_dictionary/understanding.txt'),
    'apply': BloomAnalysisWithBERTandKoBERT.load_dictionary('KR_bloom_dictionary/applying.txt'),
    'analyze': BloomAnalysisWithBERTandKoBERT.load_dictionary('KR_bloom_dictionary/analyzing.txt'),
        'evaluate': BloomAnalysisWithBERTandKoBERT.load_dictionary('KR_bloom_dictionary/evaluating.txt'),
    'create': BloomAnalysisWithBERTandKoBERT.load_dictionary('KR_bloom_dictionary/creating.txt')
}

bloom_dict_en = {
    'remember': BloomAnalysisWithBERTandKoBERT.load_dictionary('EN_bloom_dictionary/remembering.txt'),
    'understand': BloomAnalysisWithBERTandKoBERT.load_dictionary('EN_bloom_dictionary/understanding.txt'),
    'apply': BloomAnalysisWithBERTandKoBERT.load_dictionary('EN_bloom_dictionary/applying.txt'),
    'analyze': BloomAnalysisWithBERTandKoBERT.load_dictionary('EN_bloom_dictionary/analyzing.txt'),
    'evaluate': BloomAnalysisWithBERTandKoBERT.load_dictionary('EN_bloom_dictionary/evaluating.txt'),
    'create': BloomAnalysisWithBERTandKoBERT.load_dictionary('EN_bloom_dictionary/creating.txt')
}

if __name__ == "__main__":
    # 분석에 사용할 데이터 파일 경로 설정
    tag_data_path = 'or1.csv'
    bert_data_path = 'sentences_for_bert.csv'
    
    # KoBERT와 BERT 모델 경로 설정
    kobert_model_path = 'monologg/kobert'
    bert_model_path = 'bert-base-uncased'
    
    # Bloom's taxonomy 분석기 인스턴스 생성
    bloom_analyzer = BloomAnalysisWithBERTandKoBERT(
        tag_data_path=tag_data_path,
        bert_data_path=bert_data_path,
        bloom_dict_ko=bloom_dict_ko,
        bloom_dict_en=bloom_dict_en,
        kobert_model_path=kobert_model_path,
        bert_model_path=bert_model_path
    )
    
    # 동사 처리 및 분석
    bloom_analyzer.process_verbs()
    
    # Bloom 단계 분포 계산
    bloom_analyzer.calculate_bloom_distribution()
    
    # 도넛 차트 시각화
    bloom_analyzer.plot_donut_chart()
    
    # 점 그래프 시각화 (결합된 세그먼트 필요)
    merged_segments = [
        # 예시 데이터: 시작 세그먼트, 종료 세그먼트, Bloom 단계
        (0, 60, 'understand'),
        (60, 120, 'apply'),
        (120, 180, 'analyze')
    ]
    bloom_analyzer.plot_dot_graph(merged_segments)
