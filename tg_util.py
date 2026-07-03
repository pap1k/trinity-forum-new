import config
from httpx import AsyncClient, Timeout

async def announce_tg(text: str) -> int | None:
    async with AsyncClient(proxy='socks5h://127.0.0.1:9050') as client:
        url = f"https://api.telegram.org/bot{config.TG_TOKEN}/"
        params = {
            "chat_id": config.TG_ANOUNCE_ID,
            "text": text,
            "message_thread_id": config.TG_ANNOUNCE_THREAD,
        }
        response = await client.get(url+"/sendMessage", params=params, timeout=Timeout(10.0))
        if response.status_code == 200:
            return response.json().get("result", {}).get("message_id")
        else:
            return None