import os
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

async def test_connection():
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    
    if not api_id or not api_hash:
        print("❌ Erreur: TELEGRAM_API_ID ou TELEGRAM_API_HASH manquant dans le fichier .env")
        return

    client = TelegramClient('test_session', api_id, api_hash)
    
    try:
        print("Connexion au client Telegram...")
        await client.start()
        me = await client.get_me()
        print(f"✅ Connecté en tant que: {me.first_name} (@{me.username})")
        print("Votre configuration est valide !")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_connection())
