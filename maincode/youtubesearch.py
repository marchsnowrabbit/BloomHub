from flask import Flask, render_template, request
from googleapiclient.discovery import build
import isodate  # isodate 패키지를 사용하여 ISO 8601 형식 변환

app = Flask(__name__)

class YoutubeVideoapi:
    def __init__(self):
        self.developer_key = 'AIzaSyA7Qn-gNPnDQ4xgpDemtU0OzArCzL0zqvI'  # 여기에 실제 API 키를 입력하세요.
        self.youtube_api_service_name = "youtube"
        self.youtube_api_version = 'v3'

    def videolist(self, keyword):
        youtube = build(self.youtube_api_service_name, self.youtube_api_version, developerKey=self.developer_key)

        try:
            search_response = youtube.search().list(
                q=keyword,
                order='viewCount',  # 인기 있는 영상으로 정렬
                part='snippet',
                maxResults=20  # 상위 20개 영상
            ).execute()

            video_ids = []
            videos = []
            for item in search_response['items']:
                video_id = item['id'].get('videoId')
                if video_id:
                    video_ids.append(video_id)
                    videos.append({
                        'title': item['snippet']['title'],
                        'videoId': video_id,
                        'thumbnail': item['snippet']['thumbnails']['default']['url'],
                        'channelTitle': item['snippet']['channelTitle']
                    })

            if video_ids:
                videos_response = youtube.videos().list(
                    id=','.join(video_ids),
                    part='contentDetails,statistics'
                ).execute()

                for i, video in enumerate(videos_response['items']):
                    duration = self.convert_duration(video['contentDetails']['duration'])  # 포맷 변환 호출
                    view_count = video['statistics'].get('viewCount', 0)
                    videos[i]['duration'] = duration
                    videos[i]['viewCount'] = view_count

            return videos

        except Exception as e:
            print(f"오류 발생: {e}")
            return []

    def convert_duration(self, duration):
        """ISO 8601 형식의 지속 시간을 시간과 분 단위로 변환합니다."""
        duration_obj = isodate.parse_duration(duration)
        total_minutes = int(duration_obj.total_seconds() // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}시간 {minutes}분" if hours > 0 else f"{minutes}분"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    keyword = request.form['keyword']
    video_api = YoutubeVideoapi()
    videos = video_api.videolist(keyword)
    return render_template('results.html', videos=videos, keyword=keyword)

if __name__ == "__main__":
    app.run(debug=True)
