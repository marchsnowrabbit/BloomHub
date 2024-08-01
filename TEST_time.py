import time
from konlpy.tag import Komoran, Okt

class TextAnalyzer:
    def __init__(self, segments, stopwords):
        self.segments = segments
        self.stopwords = stopwords

    def analyze_with_komoran(self):
        komoran = Komoran()
        start_time = time.time()
        for segment in self.segments:
            analyzed_segment = komoran.pos(segment['text'])
            nouns = [word for word, pos in analyzed_segment if pos.startswith('NN')]
            verbs = [word for word, pos in analyzed_segment if pos.startswith('VV')]
            verbs_lemma = self.get_verbs_lemma_komoran(analyzed_segment, komoran)
            filtered_nouns = [word for word in nouns if word not in self.stopwords]
            filtered_verbs = [word for word in verbs_lemma if word not in self.stopwords]
            segment['nouns'] = filtered_nouns
            segment['verbs'] = filtered_verbs
        end_time = time.time()
        return end_time - start_time

    def analyze_with_okt(self):
        okt = Okt()
        start_time = time.time()
        for segment in self.segments:
            analyzed_segment = okt.pos(segment['text'], stem=True)
            nouns = [word for word, pos in analyzed_segment if pos.startswith('N')]
            verbs = [word for word, pos in analyzed_segment if pos.startswith('V')]
            filtered_nouns = [word for word in nouns if word not in self.stopwords]
            filtered_verbs = [word for word in verbs if word not in self.stopwords]
            segment['nouns'] = filtered_nouns
            segment['verbs'] = filtered_verbs
        end_time = time.time()
        return end_time - start_time

    def get_verbs_lemma_komoran(self, analyzed_segment, komoran):
        lemmas = []
        for word, pos in analyzed_segment:
            if pos.startswith('VV'):
                lemmas.append(komoran.morphs(word)[0])
        return lemmas

# Example usage
segments = [{'text': '나는 밥을 먹었다.' * 100}]  # 반복해서 데이터 양을 늘림
stopwords = ['나', '을']

analyzer = TextAnalyzer(segments, stopwords)

komoran_time = analyzer.analyze_with_komoran()
okt_time = analyzer.analyze_with_okt()

print(f"Komoran 분석 시간: {komoran_time:.4f} 초")
print(f"Okt 분석 시간: {okt_time:.4f} 초")
