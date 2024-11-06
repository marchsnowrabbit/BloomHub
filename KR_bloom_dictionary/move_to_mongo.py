import os
import pandas as pd
from pymongo import MongoClient

# MongoDB 클라이언트 설정
client = MongoClient("mongodb+srv://beansu:2001%3FSsb0@bloomcluster.a84bi.mongodb.net/BloomHub?retryWrites=true&w=majority")
db = client["BloomHub"]
collection = db["bloom_dictionary"]

# CSV 파일을 읽고 MongoDB에 삽입하는 함수
def upload_dictionary_to_mongo(directory, language):
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            stage = filename.split('.')[0]  # 파일 이름에서 단계 추출 (예: 'analyzing', 'applying' 등)
            file_path = os.path.join(directory, filename)

            # CSV 파일 읽기
            data = pd.read_csv(file_path, header=None, names=["word"])
            words = data["word"].tolist()

            # MongoDB에 삽입
            document = {
                "language": language,
                "stage": stage,
                "words": words
            }
            collection.update_one(
                {"language": language, "stage": stage},
                {"$set": document},
                upsert=True
            )
            print(f"Inserted {stage} data for {language}")

# 한국어 및 영어 사전 업로드
upload_dictionary_to_mongo("KR_bloom_dictionary", "Korean")
upload_dictionary_to_mongo("EN_bloom_dictionary", "English")
