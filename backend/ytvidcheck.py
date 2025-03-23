from googleapiclient.discovery import build

YOUTUBE_API_KEY = "AIzaSyCDL9D894_uMOUG3pe9ae4inLwpRMCf_BsRE"
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
request = youtube.search().list(q="Python programming", part="snippet", type="video", maxResults=3)
response = request.execute()
print(response)
