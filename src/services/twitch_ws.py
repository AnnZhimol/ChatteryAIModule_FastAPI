import time

import websockets
import asyncio
import re
import base64

from src.grpc.grpc_client import GRPCClient
from src.services.predict_sentence import PredictSentence
from src.services.predict_sentiment import PredictSentiment
from src.services.spam_detection import SpamDetection


class TwitchWS:
    def __init__(self, url: str, nick: str, user: str, password: str, trans_id: str):
        self.url = url
        self.nick = nick
        self.user = user
        self.password = password
        self.channel = url.split('/')[-1]
        self.messages_data = []
        self.ws = None
        self.analyzer = SpamDetection()
        self.predictor_sentence = PredictSentence()
        self.predictor_sentiment = PredictSentiment()
        self.grpc_client = GRPCClient()
        self.trans_id = trans_id

    @staticmethod
    async def send_ping(ws):
        while True:
            await asyncio.sleep(300)
            try:
                await ws.send("PONG")
            except Exception as e:
                print(f"Error sending PING: {e}")
                break

    async def on_message(self, ws, message):
        print(f"Received: {message}")

        if "PONG" in message:
            await ws.send("PING")
            print("Sent PONG")
            return

        privmsg_pattern = re.compile(
            r'@(?P<tags>[^ ]+) :(?P<user>[^!]+)![^ ]+ PRIVMSG #(?P<channel>[^ ]+) :(?P<message>.+)')
        match = privmsg_pattern.match(message)
        if match:
            tags = match.group('tags')
            user = match.group('user')
            channel = match.group('channel')
            message_text = match.group('message')

            if user.lower() in ['nightbot', 'streamelements', 'moobot']:
                print(f"Skipped message from bot: {user}")
                return

            if self.analyzer.analyze_comment(message_text) > 70:
                print(f"Skipped message: {self.analyzer.analyze_comment(message_text)}")
                return

            tag_dict = {}
            for tag in tags.split(';'):
                key, value = tag.split('=', 1)
                tag_dict[key] = value if value else None

            parent_user_name = tag_dict.get('reply-parent-display-name')
            parent_message = tag_dict.get('reply-parent-msg-body')
            sentence_type = self.predictor_sentence.get_class(message_text)
            sentiment_type = self.predictor_sentiment.get_class(message_text)

            parent_user = parent_user_name.replace("\\s", " ") if parent_user_name else None
            parent_message_text = parent_message.replace("\\s", " ") if parent_message else None

            self.grpc_client.send_message(
                user=user,
                message=message_text,
                sentence_type=str(sentence_type),
                sentiment_type=str(sentiment_type),
                parent_user=parent_user,
                parent_message=parent_message_text,
                channel=channel,
                timestamp=str(time.time()),
                trans_id=self.trans_id
            )

            self.messages_data.append([
                user,
                message_text,
                sentence_type,
                sentiment_type,
                parent_user,
                parent_message_text,
                channel,
                int(time.time())
            ])

    @staticmethod
    async def on_error(ws, error):
        print(f"Error: {error}")

    @staticmethod
    async def on_close(ws):
        if ws:
            try:
                await ws.close()
                print("WebSocket closed successfully")
            except Exception as e:
                print(f"Error closing WebSocket: {e}")

    async def on_open(self, ws):
        print(f"WebSocket connection opened to {ws.channel}")
        if self.nick and self.user:
            await ws.send("CAP REQ :twitch.tv/tags twitch.tv/commands")
            await ws.send(f"PASS {self.password}")
            await ws.send(f"NICK {self.nick}")
            await ws.send(f"USER {self.user} 8 * :{self.user}")
            await ws.send(f"JOIN #{ws.channel}")
        else:
            print("Error: NICK or USER not found yet.")

        asyncio.create_task(self.send_ping(ws))

    async def start_websocket(self):
        uri = "wss://irc-ws.chat.twitch.tv:443"
        async with websockets.connect(uri) as ws:
            self.ws = ws
            ws.channel = self.channel
            await self.on_open(ws)
            try:
                async for message in ws:
                    await self.on_message(ws, message)
            except Exception as e:
                await self.on_error(ws, e)
            finally:
                await self.on_close(ws)
                self.ws = None