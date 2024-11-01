import time
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go
from sklearn.feature_extraction.text import TfidfVectorizer
from openai import OpenAI, max_retries
import os



class BloomAnalysisWithGPTandDictionary:
    def __init__(self, word_data_path, sentence_data_path, bloom_dict_ko, bloom_dict_en):
        self.word_data = pd.read_csv(word_data_path)
        self.sentence_data = pd.read_csv(sentence_data_path)

        self.bloom_dict_ko = bloom_dict_ko
        self.bloom_dict_en = bloom_dict_en
        self.bloom_priority = {
            'remember': 6, 'understand': 5, 'apply': 4, 
            'analyze': 3, 'evaluate': 2, 'create': 1
        }

    @staticmethod
    def load_dictionary(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file]

    def detect_language(self):
        # 벡터화된 언어 감지
        self.word_data['language'] = self.word_data['word'].str.contains('[\u3131-\uD79D]').map(
            {True: 'Korean', False: 'English'}
        )


    def process_verbs(self):
        # 언어 감지 호출
        self.detect_language()

        # 동사만 필터링
        verbs = self.word_data[self.word_data['pos'] == 'verb'].copy()

        # 동사별 사용 횟수를 'start_time', 'end_time' 기준으로 그룹화
        self.verb_counts = verbs.groupby(['start_time', 'end_time', 'word', 'language']).size().reset_index(name='count')

        # Bloom 단계 결정 함수에 'start_time', 'end_time' 전달
        self.verb_counts['bloom_stage'] = self.verb_counts.apply(
            lambda row: self.determine_final_bloom_stage(row['word'], row['language'], row['start_time'], row['end_time']),
            axis=1
        )

    def tag_bloom_stage(self, word, language):
        # 단순 사전 탐색 (완전 일치)
        bloom_dict = self.bloom_dict_ko if language == 'Korean' else self.bloom_dict_en
        for stage, words in bloom_dict.items():
            if word in words:
                return stage
        return 'unknown'
    
    def gpt_bloom_classification(self, grouped_sentences):
        client = OpenAI(api_key="your-api-key")
       
        # 시스템 메시지 설정으로 Bloom 단계 분류 유도
        messages = [
            {"role": "system", "content": "You are a helpful assistant that classifies text into Bloom's Taxonomy stages."}
        ]

        """
        블룸텍소노미 동사표를 csv파일로 만들고, combined_sentences + csv를 함께 gpt에 입력으로 사용
        (dictionary text file을 csv로 구성해서 유지)
        gpt 출력형식 지정
        e.g. 
        """
        results = {}  # 결과를 저장할 딕셔너리
        for (start_time, end_time), combined_text in grouped_sentences.items():
            user_content = (
                f"The following text is from {start_time}s to {end_time}s:\n\n"
                f"{combined_text}\n\n"
                "Please break this text into complete sentences. Then, classify each sentence "
                "according to Bloom's Taxonomy as one of the following stages: 'Remember', 'Understand', "
                "'Apply', 'Analyze', 'Evaluate', or 'Create'.\n\n"
                "Format each sentence with its classification like this:\n"
                "- Sentence: <Complete Sentence>\n- Stage: <Bloom's Taxonomy Stage>"
            )
            messages.append({"role": "user", "content": user_content})

            for attempt in range(max_retries):
                try:
                    # GPT 모델에 요청 전송
                    completion = client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        temperature=0.0,
                        timeout=30
                    )
                
                    # 올바른 형식으로 응답 추출
                    raw_response = completion.choices[0].message.content
                    print("\nGPT Processed Response:\n", raw_response)

                    # 응답을 줄 단위로 나누고, 빈 줄 제거
                    response_lines = [line.strip() for line in raw_response.split('\n') if line.strip()]
                
                    # 필요한 부분만 추출하여 결과 저장
                    results[(start_time, end_time)] = response_lines if response_lines else 'unknown'
                    break  # 성공적으로 처리된 경우 루프 종료

                except (KeyError, IndexError, AttributeError) as e:
                    print(f"Error for segment {start_time}-{end_time}: {e}.")
                    results[(start_time, end_time)] = 'unknown'
                    break
            
                except Exception as e:
                    print(f"Attempt {attempt + 1} for segment {start_time}-{end_time} failed with error: {e}. Retrying...")
                    time.sleep(2 ** attempt)

        # 구간에 대한 결과를 반환
        return [results.get((start_time, end_time), 'unknown') for (start_time, end_time) in grouped_sentences.keys()]
    
    def determine_final_bloom_stage(self, word, language, start_time, end_time):
        # 단어 및 문장 기반 Bloom 단계 결정
        word_based_stage = self.tag_bloom_stage(word, language)

        # 해당 시간 구간에 해당하는 문장 필터링
        sentences = self.sentence_data[
            (self.sentence_data['start_time'] == start_time) & 
            (self.sentence_data['end_time'] == end_time)
        ]['word'].values

        # 문장이 없을 경우 기본값 설정
        if len(sentences) == 0:
            sentence_based_stage = 'unknown'
        else:
            # numpy 배열을 리스트로 변환 후 GPT 호출
            grouped_sentences = {(start_time, end_time): list(sentences)}
            results = self.gpt_bloom_classification(grouped_sentences)
        
            # 모든 문장에 대한 Bloom 단계 결과 수집
            stages = [result for result in results if isinstance(result, str)]

            if not stages:
                sentence_based_stage = 'unknown'
            else:
                # 각 단계의 빈도를 계산
                from collections import Counter
                stage_counts = Counter(stages)
                # 가장 빈도가 높은 단계 선택
                sentence_based_stage = stage_counts.most_common(1)[0][0]

        # 최종 단계 결정 (우선순위 비교)
        if word_based_stage == 'unknown':
            return sentence_based_stage
        elif sentence_based_stage == 'unknown':
            return word_based_stage
        else:
            return self.choose_better_stage(word_based_stage, sentence_based_stage)

    def calculate_bloom_distribution(self):
        # 구간별 Bloom 단계 분포 계산
        self.bloom_distribution = self.verb_counts.groupby(
            ['start_time', 'end_time', 'bloom_stage']
        ).size().unstack(fill_value=0)
    
        # 각 구간에서 가장 빈도가 높은 Bloom 단계 결정
        self.bloom_distribution['decided_stage'] = self.bloom_distribution.drop(columns='unknown').idxmax(axis=1)

    def decide_bloom_stage(self, row):
        # 각 구간에서 가장 빈도가 높은 Bloom 단계 결정
        stages = row.drop('unknown').to_dict()
        if not stages:
            return 'unknown'
        return max(stages, key=lambda stage: (stages[stage], -self.bloom_priority[stage]))

    def merge_segments(self):
        # 동일한 Bloom 단계를 갖는 구간 병합
        merged_segments = []
        start_time, prev_stage, prev_end = None, None, None

        for idx, row in self.bloom_distribution.iterrows():
            stage = row['decided_stage']
            current_start = idx[0]  # 'start_time'
            current_end = idx[1]    # 'end_time'

            if stage != prev_stage:
                # 이전 구간이 존재하면 병합된 구간으로 추가
                if prev_stage is not None:
                    merged_segments.append((start_time, prev_end, prev_stage))
                # 새로운 구간 시작
                start_time = current_start

            # 현재 구간의 끝 시간 갱신
            prev_end = current_end
            prev_stage = stage

        # 마지막 구간 추가
        if prev_stage is not None:
            merged_segments.append((start_time, prev_end, prev_stage))

        return merged_segments


    def plot_donut_chart(self):
        # Bloom 단계별 도넛 차트
        bloom_counts = self.verb_counts['bloom_stage'].value_counts().reset_index()
        bloom_counts.columns = ['bloom_stage', 'counts']
        bloom_counts = bloom_counts[bloom_counts['bloom_stage'] != 'unknown']

        color_map = {
            'remember': '#8290c4', 'understand': '#88c1e8',
            'apply': '#74ac80', 'analyze': '#b1d984',
            'evaluate': '#fae373', 'create': '#fb8976'
        }

        fig = px.pie(
            bloom_counts, names='bloom_stage', values='counts', hole=0.5,
            color='bloom_stage', color_discrete_map=color_map
        )
        fig.show()

    def plot_dot_graph(self, merged_segments):
        # 시간 흐름에 따른 Bloom 단계 그래프
        bloom_stage_mapping = {
            'remember': 1, 'understand': 2, 'apply': 3,
            'analyze': 4, 'evaluate': 5, 'create': 6
        }
        color_map = {
            'remember': '#8290c4', 'understand': '#88c1e8',
            'apply': '#74ac80', 'analyze': '#b1d984',
            'evaluate': '#fae373', 'create': '#fb8976'
        }

        final_result = pd.DataFrame(merged_segments, columns=['start_segment', 'end_segment', 'bloom_stage'])
        final_result['bloom_stage_numeric'] = final_result['bloom_stage'].map(bloom_stage_mapping)
        final_result['bloom_color'] = final_result['bloom_stage'].map(color_map)

        #선없는 도트 그래프
        dot_trace = go.Scatter(
            x=final_result['start_segment'], y=final_result['bloom_stage_numeric'],
            mode='markers', marker=dict(size=10, color=final_result['bloom_color']), name='Bloom Stages'
        )

        layout = go.Layout(
            title='Bloom Stages Over Time', xaxis_title='Time (seconds)', yaxis_title='Bloom Stage (numeric)',
            yaxis=dict(tickvals=[1, 2, 3, 4, 5, 6], ticktext=['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']),
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
    
    #명사 분석 함수
    def analyze_nouns(self, top_n=5):
        nouns = self.word_data[self.word_data['pos'] == 'noun']
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
bloom_analysis = BloomAnalysisWithGPTandDictionary('words.csv','sentences_for_gpt.csv', bloom_dict_ko, bloom_dict_en)
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

# TF-IDF로 명사 5개 출력
top_nouns = bloom_analysis.analyze_nouns()
print("\nTop 5 Nouns by TF-IDF:")
for noun in top_nouns:
    print(noun)