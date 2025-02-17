import logging
import random
import requests
from botbuilder.core import (
    ActivityHandler,
    MessageFactory,
    TurnContext,
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings
)
from botbuilder.schema import Activity, ActivityTypes
from aiohttp import web
from bs4 import BeautifulSoup
import aiohttp

APP_ID = "" 
APP_PASSWORD = ""
BASE_URL = "http://localhost:8000/api/v1"
token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6IllUY2VPNUlKeXlxUjZqekRTNWlBYnBlNDJKdyJ9.eyJhdWQiOiIwMTMxNGQxNC1jMWQ1LTQwOWUtYjc1Yy0wODJkY2ZkYzUyOWYiLCJpc3MiOiJodHRwczovL2xvZ2luLm1pY3Jvc29mdG9ubGluZS5jb20vZjE1Y2YxYzktMTk3My00YjM0LTkzZWMtYzA3ODkzOTc3NDYzL3YyLjAiLCJpYXQiOjE3MzkxNzc5NDcsIm5iZiI6MTczOTE3Nzk0NywiZXhwIjoxNzM5MTgxODQ3LCJuYW1lIjoiVmlkaHlhICBWaWpheWFuIiwibm9uY2UiOiIwMTk0ZWYxYi04YmFiLTc0ZTItYjkwMi1jYWQzZjcyMGJhMjYiLCJvaWQiOiJlMTJiZDFkOS1lNGZiLTQzNzItYjAzZS1lZDM2MTY3YjRjYTEiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJWaWRoeWEuVmlqYXlhbkBhbGZlcml4LmNvbSIsInJoIjoiMS5BWHdBeWZGYzhYTVpORXVUN01CNGs1ZDBZeFJOTVFIVndaNUF0MXdJTGNfY1VwLTdBRTE4QUEuIiwic2lkIjoiMDAyMDEzMDktZGY1YS00Y2VmLWZmMzktOTZkMTg4MDdkZGRlIiwic3ViIjoieGdrVHEyME81NG82RmdGMmpFUWp4akZ3N0hCcUUyaFpXY3JCQWFyRk01ZyIsInRpZCI6ImYxNWNmMWM5LTE5NzMtNGIzNC05M2VjLWMwNzg5Mzk3NzQ2MyIsInV0aSI6IkRrRnJBa19ZMzBheFVGeXRHdTBoQUEiLCJ2ZXIiOiIyLjAifQ.Wxd9_RAFmILJso9Ihn9nYoA4HdH8mldQjeB8ZOVYd_9k-CgKxayWCNQneBUAoPX6olEpBtvqn5N9zmBv9aCJ1P6zqOx517lHf2hTXvxlr19oUNHvHBoliVtO2N1U9g4Eicvt0RXEvWHP4t3oxIuily_AE44TYhm5JnaKO-EqnnkDIlNg8v_1QaUSb5C8fSlMRTqT2mGdOIoKDsUQAMv9Om1LS498jQgKXnk6LvZg8QzeDQ3543cKKUFzwCTaqr4RnJ-dTFlxFPz4SHU8C27KecvL8Apc-spHNYpsbDMb2uXSdz0FBWvi9kS3yfchpHZVGeMeLPUHL6r0KjtzeqxxZQ'
model = 'gemini'
#buddy-chatbot
adapter_settings = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
adapter = BotFrameworkAdapter(adapter_settings)

class EventDrivenBot(ActivityHandler):
    def __init__(self):
        super(EventDrivenBot, self).__init__()
        
    async def on_message_activity(self, turn_context: TurnContext):
        print(f"inside on_message_activity")
        user_input = turn_context.activity.text.strip().lower()
        if "hello" in user_input or "hi" in user_input:
            response = await self.greeting(turn_context)
            print(response)
        else:
            print(f"In else block")
            response = await self.ask_question(token, user_input, model)
        await turn_context.send_activity(response)

    async def greeting(self, turn_context: TurnContext):
        print(f"inside greet and get")
        greet_response = random.choice(["Hello!", "Hi there!", "Hey!"])
        help_message = "How can I help you?"
        return f"{greet_response} {help_message}"
        
    async def ask_question(self, token: str, question: str, model: str):
        print(f"inside ask_question")
        url = f"{BASE_URL}/chat"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        payload = {
            'question': question,
            'model': model
        }
        print(payload)
        try:
            async with aiohttp.ClientSession() as session: 
                async with session.post(url, json=payload, headers=headers) as response:
                    response.raise_for_status()

                    if 'application/json' in response.headers.get('Content-Type', ''):
                        try:
                            api_data = await response.json()
                            if 'response' in api_data:
                                html_content = api_data['response'] 
                                soup = BeautifulSoup(html_content, 'html.parser')
                                text_content = soup.get_text(separator="\n")
                                return text_content
                            else:
                                return "Response field is missing in the JSON data."
                        except Exception as e:
                            return f"Error parsing the JSON response: {e}"
                    else:
                        return "Response is not JSON. Skipping JSON parsing."
        except aiohttp.ClientError as error:
            return f"Error fetching data from the API: {error}"

bot = EventDrivenBot()

async def handle_message(request):
    print(f"inside handle_message")
    try:
        body = await request.json()
        if not body:
            return web.Response(text="Empty request body", status=400)
        try:
            activity = Activity().deserialize(body)
        except Exception as e:
            return web.Response(text="Invalid activity data", status=400)

        if not activity or not hasattr(activity, 'channel_id') or not activity.channel_id:
            #print(f"Invalid activity data")
            return web.Response(text="Invalid activity data", status=400)
        try:
            response = await adapter.process_activity(activity, "", bot.on_turn)
        except Exception as e:
            return web.Response(text="Error processing activity", status=500)
        return web.Response(text="OK")

    except Exception as e:
        return web.Response(text="Error processing message", status=500)


app = web.Application()
app.router.add_post("/api/messages", handle_message)

if __name__ == "__main__":
    web.run_app(app, host="localhost", port=3978)
