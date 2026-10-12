import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise RuntimeError("Faltan TELEGRAM_TOKEN o CHAT_ID en el archivo .env")

CHAT_ID = int(CHAT_ID)