"""
Script para generar un SESSION_STRING nuevo e independiente para Telethon.
Correr localmente (no en Render). Pide API_ID, API_HASH, numero de telefono
y el codigo que llega por Telegram. Al final imprime la cadena para pegarla
en las variables de entorno del servicio "bot prueba" en Render.

No guarda ni sube nada a ningun lado: la sesion vive solo en la variable
SESSION_STRING que tu copias manualmente.
"""

from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = int(input("API_ID: ").strip())
api_hash = input("API_HASH: ").strip()

with TelegramClient(StringSession(), api_id, api_hash) as client:
    session_string = client.session.save()
    print("\n=== Copia esta linea completa en Render (variable SESSION_STRING) ===\n")
    print(session_string)
    print("\n=======================================================================")
