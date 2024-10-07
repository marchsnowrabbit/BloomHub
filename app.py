from flask import Flask, render_template, request
from googleapiclient.discovery import build
import datetime as dt

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
                order='viewCount',
                part='snippet',
                maxResults=20
            ).execute()

            video_ids = []
            videos = []
            for item in search_response['items']:
                video_id = item['id'].get('videoId')
                if video_id:
                    video_ids.append(video_id)
                    videos.append({
                        'title': item['snippet']['title'],
                        'videoId': video_id
                    })

            return videos

        except Exception as e:
            print(f"Error occurred: {e}")
            return []


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
