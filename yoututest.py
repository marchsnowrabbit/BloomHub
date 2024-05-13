from youtube_transcript_api import YouTubeTranscriptApi

srt = YouTubeTranscriptApi.get_transcript("s8l6r4-P__k", languages=['ko'])
with open ("subtitles.txt", "w", encoding='utf-8') as f:
    for i in srt:

        f.write("{}\n". format (i))
