from sklearn.model_selection import train_test_split
from transformers import Trainer, TrainingArguments

# 데이터셋 준비 (train.csv의 구조가 필요한 데이터와 레이블이 포함되어 있다고 가정)
data = pd.read_csv('your_dataset.csv')
train_data, test_data = train_test_split(data, test_size=0.2)

# BERT 토크나이저로 텍스트 토큰화
train_encodings = self.bert_tokenizer(list(train_data['text']), truncation=True, padding=True)
test_encodings = self.bert_tokenizer(list(test_data['text']), truncation=True, padding=True)

# 데이터셋 클래스 정의
class BloomDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

train_dataset = BloomDataset(train_encodings, list(train_data['label']))
test_dataset = BloomDataset(test_encodings, list(test_data['label']))

# 모델 초기화
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=6)

# 훈련 인자 설정
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=3,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=16,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir='./logs',
)

# Trainer 생성
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
)

# 모델 학습
trainer.train()

# 학습된 모델 저장
model.save_pretrained('./my_model')
self.bert_tokenizer.save_pretrained('./my_model')
