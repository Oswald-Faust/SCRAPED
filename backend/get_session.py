import os
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

print("Chargement des variables...")
load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")

if not API_ID or not API_HASH:
    print("ERREUR: API_ID ou API_HASH manquants dans le .env !")
    exit(1)

print(f"Connexion avec API_ID: {API_ID}...")

# Utilisation d'un bloc try pour voir les erreurs
try:
    with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        print("\n--- TA STRING SESSION ---")
        session_str = client.session.save()
        print(session_str)
        print("--------------------------\n")
        print("Copie TOUTE la ligne ci-dessus.")
except Exception as e:
    print(f"ERREUR LORS DE LA CONNEXION : {e}")
