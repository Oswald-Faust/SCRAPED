import os
import re
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telethon import TelegramClient, events
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
BOT_TARGET = os.getenv("TELEGRAM_BOT_TARGET", "@paumes_bot")
SESSION_NAME = os.getenv("TELEGRAM_SESSION_NAME", "session_faust")

app = FastAPI(title="Smart Proxying API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Telegram Client Singleton
client = None

async def get_telegram_client():
    global client
    if client is None:
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await client.start()
    return client

class SearchRequest(BaseModel):
    query: str

def parse_bot_response(text: str):
    """
    Parses the raw text from @paumes_bot into a structured JSON format.
    Adapt regex based on actual bot output.
    """
    data = {
        "raw": text,
        "email": re.search(r"E-mail: (.*)", text),
        "phone": re.search(r"Téléphone: (.*)", text),
        "password": re.search(r"Mot de passe.*: (.*)", text),
        "fullname": re.search(r"Nom d'utilisateur: (.*)", text) or re.search(r"Name: (.*)", text),
        "source": re.search(r"Source: (.*)", text)
    }
    
    # Extract values from match objects
    for key in data:
        if key != "raw" and data[key]:
            data[key] = data[key].group(1).strip()
        elif key != "raw":
            data[key] = None
            
    return data

@app.post("/search")
async def search_leak(request: SearchRequest):
    if not API_ID or not API_HASH:
        raise HTTPException(status_code=500, detail="Telegram API credentials not configured.")

    tg_client = await get_telegram_client()
    
    # Create a future to capture the response
    response_future = asyncio.get_event_loop().create_future()

    # Define the handler for the specific bot response
    @tg_client.on(events.NewMessage(from_users=BOT_TARGET))
    async def handler(event):
        if not response_future.done():
            response_future.set_result(event.raw_text)
        tg_client.remove_event_handler(handler)

    try:
        # Send query to bot
        await tg_client.send_message(BOT_TARGET, request.query)
        
        # Wait for response with timeout (e.g., 30 seconds)
        raw_response = await asyncio.wait_for(response_future, timeout=30.0)
        
        # Parse and return
        parsed_data = parse_bot_response(raw_response)
        return {"status": "success", "data": parsed_data}

    except asyncio.TimeoutError:
        tg_client.remove_event_handler(handler)
        raise HTTPException(status_code=504, detail="Timeout: No response from bot.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
