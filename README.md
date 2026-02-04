# Scraped Cloud - Smart Proxying System

Ce projet est une plateforme de recherche de fuites de données utilisant un "Smart Proxying" vers un bot Telegram (`@paumes_bot`).

## Architecture

- **Frontend** : React + Vite (Design Apple-style / Glassmorphism)
- **Backend** : FastAPI + Telethon (UserBot Telegram)

## Installation

### 1. Backend

Connectez-vous à [my.telegram.org](https://my.telegram.org) pour obtenir vos identifiants API.

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Remplissez .env avec vos API_ID et API_HASH
python main.py
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

## Fonctionnement

Le site envoie une requête au backend. Le backend, via un UserBot, pose la question au bot Telegram. Une fois la réponse reçue, elle est parsée en JSON et renvoyée au frontend pour un affichage élégant.
