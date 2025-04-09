import asyncio
import time
import json
import threading

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import websockets

from src.grpc.grpc_client import GRPCClient
from src.services.predict_sentence import PredictSentence
from src.services.predict_sentiment import PredictSentiment
from src.services.spam_detection import SpamDetection


class VkWS:
    def __init__(self, channel_name: str, trans_id: str):
        self.channel_name = channel_name
        self.messages_data = []
        self.headers = {
            "Origin": "https://live.vkplay.ru",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }
        self.token = None
        self.websocket_url = None
        self.chat_channel = None
        self.ws = None
        self.analyzer = SpamDetection()
        self.predictor_sentence = PredictSentence()
        self.predictor_sentiment = PredictSentiment()
        self.grpc_client = GRPCClient()
        self.trans_id = trans_id

    async def get_connect_data(self, url: str) -> dict:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options,
        )
        driver.get(url)
        return await self.get_websocket_logs(driver)

    async def get_websocket_logs(self, driver) -> dict:
        logs = driver.get_log("performance")
        channels = []
        websocket_url, token = None, None

        for log in logs:
            message = json.loads(log["message"])

            if "Network.webSocketCreated" in message["message"]["method"]:
                websocket_url = message["message"]["params"]["url"]
                print(f"WebSocket URL: {websocket_url}")

            if "Network.webSocketFrameSent" in message["message"]["method"]:
                try:
                    payload_data = message["message"]["params"]["response"]["payloadData"]
                    if '"connect"' in payload_data:
                        token_start = payload_data.find('"token":"') + len('"token":"')
                        token_end = payload_data.find('"', token_start)
                        token = payload_data[token_start:token_end]
                        print(f"Token: {token}")
                except KeyError:
                    pass

                try:
                    payload_data = message["message"]["params"]["response"]["payloadData"]
                    if '"subscribe"' in payload_data:
                        channel_data = payload_data.split('\n')
                        for line in channel_data:
                            try:
                                subscribe_data = json.loads(line)
                                if "channel" in subscribe_data["subscribe"]:
                                    channel = subscribe_data["subscribe"]["channel"]
                                    channels.append(channel)
                            except json.JSONDecodeError:
                                continue
                except KeyError:
                    pass

        chat_channels = [channel for channel in channels if channel.startswith("channel-chat")]

        if chat_channels:
            print(f"Subscribed chat channels: {chat_channels[0]}")

        driver.quit()

        if websocket_url and token and chat_channels:
            return {"websocket_url": websocket_url, "token": token, "chat_channel": chat_channels[0]}
        else:
            print("Couldn't extract data.")
            return {}

    async def on_message(self, ws, message, tar_channel, translation_url):
        try:
            data = json.loads(message)

            if isinstance(data, dict) and not data:
                print("Get message {}. Send pong.")
                await ws.send(b'{}')
                return

            channel = data.get("push", {}).get("channel")
            if channel != tar_channel:
                return

            author_info = data.get("push", {}).get("pub", {}).get("data", {}).get("data", {}).get("author", {})
            author_name = author_info.get("displayName") or author_info.get("nick", "Неизвестный пользователь")
            author_name_parent = ""

            content_parts = []
            content_parts_parent = []
            message_content = data.get("push", {}).get("pub", {}).get("data", {}).get("data", {}).get("data", [])
            if isinstance(message_content, list):
                for item in message_content:
                    if item.get("type") == "text":
                        try:
                            text_content = json.loads(item["content"])[0]
                            content_parts.append(text_content)
                        except (json.JSONDecodeError, IndexError) as e:
                            print(f"Error while extract content: {e}")
                    if item.get("type") == "mention":
                        try:
                            text_content = item.get("displayName")
                            content_parts.append(text_content)
                        except (json.JSONDecodeError, IndexError) as e:
                            print(f"Error while extract content: {e}")
                    if item.get("type") == "link":
                        try:
                            text_content_link = item.get("url")
                            content_parts.append(text_content_link)
                        except (json.JSONDecodeError, IndexError) as e:
                            print(f"Error while extract content: {e}")
            else:
                print("Other format for data.")

            parent_data = data.get("push", {}).get("pub", {}).get("data", {}).get("data", {}).get("parent")
            if parent_data and isinstance(parent_data, dict):
                message_content_parent = parent_data.get("data", [])
                author_info_parent = parent_data.get("author", {})
                author_name_parent = author_info_parent.get("displayName") or author_info_parent.get("nick",
                                                                                                     "Неизвестный пользователь")
                if isinstance(message_content_parent, list):
                    for item in message_content_parent:
                        if item.get("type") == "mention":
                            try:
                                text_content = item.get("displayName")
                                content_parts_parent.append(text_content)
                            except (json.JSONDecodeError, IndexError) as e:
                                print(f"Error while extract content: {e}")
                        if item.get("type") == "link":
                            try:
                                text_content_link = item.get("url")
                                content_parts_parent.append(text_content_link)
                            except (json.JSONDecodeError, IndexError) as e:
                                print(f"Error while extract content: {e}")
                        elif item.get("type") == "text":
                            try:
                                text_content_parent = json.loads(item["content"])[0]
                                content_parts_parent.append(text_content_parent)
                            except (json.JSONDecodeError, IndexError) as e:
                                print(f"Error while extract content: {e}")
                else:
                    print("Error format data in parent.")
            else:
                print("Object parent is null or have other format.")

            full_message = " ".join(content_parts)
            full_message_parent = " ".join(content_parts_parent)

            if not full_message or self.analyzer.analyze_comment(full_message) > 70:
                return

            self.grpc_client.send_message(
                user=author_name,
                message=full_message,
                sentence_type=str(self.predictor_sentence.get_class(full_message)),
                sentiment_type=str(self.predictor_sentiment.get_class(full_message)),
                parent_user=author_name_parent,
                parent_message=full_message_parent,
                channel=translation_url.split('/')[-1],
                timestamp=str(time.time()),
                trans_id=self.trans_id
            )

        except json.JSONDecodeError:
            print("Error JSON:", message)
        except KeyError as e:
            print(f"Couldn't find key: {e}")
        except TypeError as e:
            print(f"Type error: {e}")

    @staticmethod
    async def on_error(ws, error):
        print("Error:", error)

    @staticmethod
    async def on_close(ws):
        if ws:
            try:
                await ws.close()
                print("WebSocket closed successfully")
            except Exception as e:
                print(f"Error closing WebSocket: {e}")

    async def on_open(self, ws):
        print("Connection opened")

        token = ws.token
        sub = ws.sub

        connect_message = json.dumps({
            "connect": {"token": token, "name": "js"},
            "id": 1
        })
        await asyncio.sleep(1)
        await ws.send(connect_message)
        SUBSCRIPTIONS = [
            {"channel": sub}
        ]

        for idx, sub in enumerate(SUBSCRIPTIONS, start=2):
            subscribe_message = json.dumps({
                "subscribe": sub,
                "id": idx
            })
            await asyncio.sleep(1)
            await ws.send(subscribe_message)

    async def start_websocket(self):
        connect_data = await self.get_connect_data(self.channel_name)
        if not connect_data:
            print("Couldn't find credentials")
            return

        uri = connect_data["websocket_url"]
        try:
            async with websockets.connect(uri, extra_headers=self.headers) as ws:
                self.ws = ws
                ws.token = connect_data["token"]
                ws.sub = connect_data["chat_channel"]
                await self.on_open(ws)
                try:
                    async for message in ws:
                        await self.on_message(ws, message, connect_data["chat_channel"], self.channel_name)
                except Exception as e:
                    await self.on_error(ws, e)
                finally:
                    await self.on_close(ws)
        except Exception as e:
            print(f"Connection failed: {e}")

    def run_websocket(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.start_websocket())

    def start(self):
        threading.Thread(target=self.run_websocket, daemon=True).start()
