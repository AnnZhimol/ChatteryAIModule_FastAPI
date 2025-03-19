from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import asyncio

from src.services.generate_credentials import GenerateCred
from src.services.twitch_ws import TwitchWS
from src.services.vk_ws import VkWS

app = FastAPI()

generator = GenerateCred()

active_connections = {}


@app.get("/connect_twitch/{channel}")
async def connect_to_channel(channel: str):
    if channel in active_connections:
        return {"status": "error", "message": "Already connected to this channel"}

    nick = user = generator.generate()
    twitch_ws = TwitchWS(
        url=f"https://www.twitch.tv/{channel}",
        nick=nick,
        user=user,
        password="SCHMOOPIIE"
    )
    active_connections[channel] = twitch_ws
    asyncio.create_task(twitch_ws.start_websocket())
    return {"status": "success", "message": f"Connected to channel {channel}"}

@app.get("/disconnect_twitch/{channel}")
async def disconnect_from_channel(channel: str):
    if channel not in active_connections:
        return {"status": "error", "message": "Not connected to this channel"}

    twitch_ws = active_connections.pop(channel)
    if twitch_ws.ws is not None:
        print(f"Closing WebSocket for channel {channel}")
        await twitch_ws.on_close(twitch_ws.ws)
    else:
        print(f"No active WebSocket for channel {channel}")
    return {"status": "success", "message": f"Disconnected from channel {channel}"}

@app.get("/connect_vk/{channel}")
async def connect_to_channel_vk(channel: str):
    if channel in active_connections:
        return {"status": "error", "message": "Already connected to this channel"}

    translation_url = f"https://live.vkvideo.ru/{channel}"
    vk_ws = VkWS(translation_url)

    active_connections[channel] = vk_ws

    try:
        asyncio.create_task(vk_ws.start_websocket())
    except Exception as e:
        print(f"Ошибка подключения: {e}")

@app.get("/disconnect_vk/{channel}")
async def disconnect_from_channel_vk(channel: str):
    if channel not in active_connections:
        return {"status": "error", "message": "Not connected to this channel"}

    vk_ws = active_connections.pop(channel)
    if vk_ws.ws is not None:
        print(f"Closing WebSocket for channel {channel}")
        await vk_ws.on_close(vk_ws.ws)
    else:
        print(f"No active WebSocket for channel {channel}")
    return {"status": "success", "message": f"Disconnected from channel {channel}"}


@app.get("/chat/{channel}", response_class=HTMLResponse)
async def get_chat(channel: str):
    if channel not in active_connections:
        return {"status": "error", "message": "Not connected to this channel"}

    twitch_ws = active_connections[channel]
    messages = twitch_ws.messages_data

    html_content = """
    <html>
        <head>
            <title>Chat for {channel}</title>
        </head>
        <body>
            <h1>Chat for {channel}</h1>
            <ul>
                {messages}
            </ul>
        </body>
    </html>
    """.format(
        channel=channel,
        messages="".join([f"<li>{msg[3]}__{msg[2]}__{msg[0]}: {msg[1]}</li>" for msg in messages])
    )

    return HTMLResponse(content=html_content)