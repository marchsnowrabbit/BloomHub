from youtube_transcript_api import YouTubeTranscriptApi

video_id = "xNMGGQIU8FU&list=PLMsa_0kAjjrdiwQykI8eb3H4IRxLTqCnP&index=3"  # 여러분이 다운로드하고자 하는 YouTube 비디오 ID를 넣어주세요
transcript_list = YouTubeTranscriptApi.list_transcripts("xNMGGQIU8FU&list=PLMsa_0kAjjrdiwQykI8eb3H4IRxLTqCnP&index=3")

# 한국어로 된 자막을 선택합니다.
transcript = transcript_list.find_transcript(['ko'])

if transcript:
    with open("subtitles.txt", "w", encoding='utf-8') as f:
        for caption in transcript.fetch():
            text = caption['text']
            f.write(f"{text}\n")
else:
    print("한국어 자막을 찾을 수 없습니다.")

print("test")