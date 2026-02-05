import os
import re
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
BOT_TARGET = os.getenv("TELEGRAM_BOT_TARGET", "@paumes_bot")
SESSION_NAME = os.getenv("TELEGRAM_SESSION_NAME", "session_faust")
STRING_SESSION = os.getenv("TELEGRAM_STRING_SESSION")

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
        if STRING_SESSION:
            client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
        else:
            client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await client.start()
    return client

class SearchRequest(BaseModel):
    query: str

class ClickRequest(BaseModel):
    message_id: int
    button_text: str

def parse_bot_response(text: str):
    """
    Dynamically parses the raw text from @paumes_bot.
    Extracts anything that follows a pattern like "Label: Value" or "Emoji Label: Value"
    """
    lines = text.split('\n')
    data = {"raw": text}
    
    # Try to extract the source (often the first line with an emoji or just text)
    if lines:
        first_line = lines[0].strip()
        if first_line and not first_line.startswith('Demande:'):
            data["Source"] = first_line.replace('**', '')

    # Regex to capture "Label: Value" or "Emoji Label: Value"
    # Group 1: Emoji (optional), Group 2: Label, Group 3: Value
    pattern = re.compile(r"(?:[\U00010000-\U0010ffff]|\d+[\u20E3])?\s*([^:]+):\s*(.*)", re.U)

    for line in lines:
        line = line.strip()
        if not line: continue
        
        match = pattern.search(line)
        if match:
            label = match.group(1).strip().replace('**', '')
            value = match.group(2).strip().replace('**', '').replace('`', '')
            
            # Skip noise like "Demande", "Temps de recherche", etc.
            if label.lower() in ["demande", "temps de recherche", "sujets faits", "nombre de résultats", "le nombre de fuites"]:
                continue
                
            data[label] = value

    return data

@app.post("/search")
async def search_leak(request: SearchRequest):
    if not API_ID or not API_HASH:
        raise HTTPException(status_code=500, detail="Telegram API credentials not configured.")

    tg_client = await get_telegram_client()
    
    captured_messages = {} # Map ID to message to handle updates
    
    async def collect_msg(event):
        captured_messages[event.message.id] = event.message

    # Listen for both new messages and edits
    tg_client.add_event_handler(collect_msg, events.NewMessage(from_users=BOT_TARGET))
    tg_client.add_event_handler(collect_msg, events.MessageEdited(from_users=BOT_TARGET))

    try:
        # Send query to bot
        await tg_client.send_message(BOT_TARGET, request.query)
        
        # Wait for initial response
        start_time = asyncio.get_event_loop().time()
        while len(captured_messages) == 0 and (asyncio.get_event_loop().time() - start_time) < 20:
            await asyncio.sleep(0.5)
            
        if len(captured_messages) == 0:
            raise HTTPException(status_code=504, detail="Timeout: No response from bot.")

        # Wait for potential follow-up messages/edits
        await asyncio.sleep(2.5)
        
        tg_client.remove_event_handler(collect_msg, events.NewMessage)
        tg_client.remove_event_handler(collect_msg, events.MessageEdited)
        
        messages = sorted(captured_messages.values(), key=lambda m: m.id)
        combined_text = "\n".join([m.text for m in messages if m.text])
        parsed_data = parse_bot_response(combined_text)
        
        # Get buttons (always from the latest message that HAS buttons)
        buttons = []
        for m in reversed(messages):
            if m.buttons:
                for row in m.buttons:
                    for btn in row:
                        buttons.append({
                            "text": btn.text, 
                            "msg_id": m.id,
                            "url": getattr(btn, 'url', None)
                        })
                break

        return {
            "status": "success", 
            "data": parsed_data, 
            "buttons": buttons
        }

    except Exception as e:
        tg_client.remove_event_handler(collect_msg, events.NewMessage)
        tg_client.remove_event_handler(collect_msg, events.MessageEdited)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/click")
async def click_button(request: ClickRequest):
    tg_client = await get_telegram_client()
    
    # Get the message state
    msg = await tg_client.get_messages(BOT_TARGET, ids=request.message_id)
    if not msg or not msg.buttons:
        raise HTTPException(status_code=404, detail="Message/Buttons non trouvés.")
    
    # Find button
    target_btn = None
    search_text = request.button_text.strip()
    
    for row in msg.buttons:
        for btn in row:
            btn_text = btn.text.strip()
            # Try exact match first, then partial match if needed
            if btn_text == search_text:
                target_btn = btn
                break
            # Fallback for emoji or weird spacing
            if search_text in btn_text or btn_text in search_text:
                target_btn = btn
                break
        if target_btn:
            break

    captured_updates = {}
    async def collect_update(event):
        captured_updates[event.message.id] = event.message

    tg_client.add_event_handler(collect_update, events.NewMessage(from_users=BOT_TARGET))
    tg_client.add_event_handler(collect_update, events.MessageEdited(from_users=BOT_TARGET))

    try:
        await target_btn.click()
        
        # Wait for any change (new msg or edit)
        start_time = asyncio.get_event_loop().time()
        while len(captured_updates) == 0 and (asyncio.get_event_loop().time() - start_time) < 15:
            await asyncio.sleep(0.5)
            
        await asyncio.sleep(1.5) # Time for all updates to settle
        tg_client.remove_event_handler(collect_update, events.NewMessage)
        tg_client.remove_event_handler(collect_update, events.MessageEdited)

        # Process results
        updates = sorted(captured_updates.values(), key=lambda m: m.id)
        
        # If no new messages, but the original message was edited, check that too
        if not updates:
            updated_msg = await tg_client.get_messages(BOT_TARGET, ids=request.message_id)
            updates = [updated_msg]

        combined_text = "\n".join([u.text for u in updates if u.text])
        parsed_data = parse_bot_response(combined_text)
        
        buttons = []
        for m in reversed(updates):
            if m.buttons:
                for row in m.buttons:
                    for btn in row:
                        buttons.append({
                            "text": btn.text, 
                            "msg_id": m.id,
                            "url": getattr(btn, 'url', None)
                        })
                break
        
        # If the menu was "reduced", maybe there are no buttons. 
        # But we should always return buttons if available.

        return {
            "status": "success",
            "data": parsed_data,
            "buttons": buttons
        }
    except Exception as e:
        tg_client.remove_event_handler(collect_update, events.NewMessage)
        tg_client.remove_event_handler(collect_update, events.MessageEdited)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
