from googleapiclient.discovery import build
import os
from newspaper import Article, Config
import datetime
from langfuse import observe

class Tools():
    # Normal response
    @observe(name = "Normal Response")
    def normalResponse(self):
        pass
        return

    # search engine
    def google_engine(self,query, **kwargs):
        service = build("customsearch", "v1", developerKey=os.getenv("GOOGLE_API_KEY"))
        results = service.cse().list(q=query, cx=os.getenv("CSE_ID"), gl = "id",**kwargs).execute()
        formatted_results = []
        for result in results['items']:
            title = result.get('title')
            link = result.get('link')
            snippet = result.get('snippet')
            formatted_results.append({
                'title': title,
                'link': link,
                'snippet': snippet
            })
        return formatted_results

    # Google search
    @observe(name = "Google Search")
    def search_google(self,query:str):
        results = self.google_engine(query, num=10)
        function_output = {
            'tool_call_id': "1",
            'contents':{
                "function_name": "search_google",
                "content": results,
            }
        }
        return function_output

    # Open web
    @observe(name = "Open web")
    def open_webpage(self, urls):
        config = Config()
        config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        webContent = []
        for url in urls:
            article = Article(url,config=config)
            try:
                article.download()
                article.parse()
            except Exception as e:
                webContent.append({
                    'title': "Unable to fetch article",
                    'text': "Unable to fetch article",
                })
            webContent.append({
                    'title': article.title,
                    'text': article.summary,
                })
        function_output = {
            'tool_call_id': "2",
            'content': webContent,
        }
        return function_output
    # Get current date and time
    @observe(name = "Get current date and time")
    def get_current_date_and_time(self):
        datetime_obj = datetime.datetime.now()
        function_output = {
            'tool_call_id': "3",
            'contents':{
                "function_name": "get_current_date_and_time",
                "content": datetime_obj.strftime("%Y-%m-%d %H:%M:%S"),
            }
        }
        return function_output

    # Search youtube video
    @observe(name = "Search youtube video")
    def search_youtube_video(self,keyword):
        youtube = build('youtube', 'v3', developerKey=os.getenv("YOUTUBE_API_KEY"))
        request = youtube.search().list(
            part="snippet",
            maxResults=10,
            q=keyword,
            type="video"
        )
        results = request.execute()

        formatted_results = []

        for result in results['items']:
            title = result['snippet']['title']
            link = f"https://www.youtube.com/watch?v={result['id']['videoId']}"
            snippet = result['snippet']['description']
            published_at = result['snippet']['publishedAt']
            formatted_results.append({
                'channel_title': result['snippet']['channelTitle'],
                'title': title,
                'link': link,
                'snippet': snippet,
                'published_at': published_at
            })
        function_output = {
            'tool_call_id': "4",
            'contents':{
                "function_name": "search_youtube_video",
                "content": formatted_results,
            }
        }
        return function_output