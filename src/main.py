from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import asyncio

from src.services.generate_credentials import GenerateCred
from src.services.twitch_ws import TwitchWS
from src.services.vk_ws import VkWS

app = FastAPI()

generator = GenerateCred()

active_connections = {}


@app.get("/connect_twitch/{channel}/{id}")
async def connect_to_channel(channel: str, id: str):
    url = f"https://www.twitch.tv/{channel}"

    if id in active_connections:
        return {
            "status": "error",
            "message": f"Already connected to channel {channel}.",
            "url": url,
            "id": id
        }

    nick = user = generator.generate()
    twitch_ws = TwitchWS(
        url=url,
        nick=nick,
        user=user,
        password="SCHMOOPIIE",
        trans_id=id
    )

    active_connections[id] = twitch_ws
    asyncio.create_task(twitch_ws.start_websocket())
    return {
        "status": "success",
        "message": f"Successful connected to channel {channel}.",
        "url": url,
        "id": id
    }

@app.get("/disconnect_twitch/{channel}/{id}")
async def disconnect_from_channel(channel: str, id: str):
    url = f"https://www.twitch.tv/{channel}"
    if id not in active_connections:
        return {
            "status": "error",
            "message": f"Not connected to channel {channel}.",
            "url": url,
            "id": id
        }

    twitch_ws = active_connections.pop(id)

    if twitch_ws.ws is not None:
        print(f"Closing WebSocket for channel {channel}")
        await twitch_ws.on_close(twitch_ws.ws)
    else:
        print(f"No active WebSocket for channel {channel}")

    return {
        "status": "success",
        "message": f"Disconnected from channel {channel}.",
        "url": url,
        "id": id
    }

@app.get("/connect_vk/{channel}/{id}")
async def connect_to_channel_vk(channel: str, id: str):
    translation_url = f"https://live.vkvideo.ru/{channel}"

    if id in active_connections:
        return {
            "status": "error",
            "message": f"Already connected to channel {channel}.",
            "url": translation_url,
            "id": id
        }

    vk_ws = VkWS(translation_url, id)

    active_connections[id] = vk_ws

    try:
        vk_ws.start()
        return {
            "status": "success",
            "message": f"Successful connected to channel {channel}.",
            "url": translation_url,
            "id": id
        }
    except Exception as e:
        print(f"Error while connect: {e}")

@app.get("/disconnect_vk/{channel}/{id}")
async def disconnect_from_channel_vk(channel: str, id: str):
    translation_url = f"https://live.vkvideo.ru/{channel}"
    if id not in active_connections:
        return {
            "status": "error",
            "message": f"Not connected to channel {channel}",
            "url": translation_url,
            "id": id
        }

    vk_ws = active_connections.pop(id)

    if vk_ws.ws is not None:
        print(f"Closing WebSocket for channel {channel}")
        await vk_ws.on_close(vk_ws.ws)
    else:
        print(f"No active WebSocket for channel {channel}")

    return {
        "status": "success",
        "message": f"Disconnected from channel {channel}",
        "url": translation_url,
        "id": id
    }


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