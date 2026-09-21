import telebot
from telebot import apihelper
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
apihelper.ENABLE_MIDDLEWARE = True
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio
import os
import threading
import re
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

# --- SERVIDOR WEB DE SALUD PARA RENDER ---
class FakeServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("BOT HUGO ACTUALIZADO - VERSION 3.2 🚀".encode("utf-8"))

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

def iniciar_servidor_falso():
    puerto = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', puerto), FakeServer)
    print(f"📡 Servidor escuchando en el puerto {puerto}")
    server.serve_forever()

threading.Thread(target=iniciar_servidor_falso, daemon=True).start()

# --- CONFIGURACIÓN MEDIANTE VARIABLES DE ENTORNO ---
try:
    API_ID = int(os.environ["API_ID"])
    API_HASH = os.environ["API_HASH"]
    BOT_TOKEN = os.environ["BOT_TOKEN"]
except KeyError as e:
    raise ValueError(f"❌ Falta variable de entorno obligatoria: {e}")

TXT_FRANCHESCO = "FRANCHESCO"
TXT_GHOSTOPS   = "DF VIP"
# TXT_KIMICO     = "K1M1CO B0Tx"  # [PAUSADO]

USER_NORTH_BOT = "northdatabasicbot"
USER_LIAM_BOT  = "Yinwodataa_botx"

SESSION_STRING = os.environ.get("SESSION_STRING", None)

bot = telebot.TeleBot(BOT_TOKEN)

@bot.middleware_handler(update_types=['message'])
def normalizar_comandos_minusculas(bot_instance, message):
    if message.text and message.text.startswith('/'):
        partes = message.text.split(maxsplit=1)
        comando_minuscula = partes[0].lower()
        if len(partes) > 1:
            message.text = f"{comando_minuscula} {partes[1]}"
        else:
            message.text = comando_minuscula

if SESSION_STRING:
    print("🔐 Iniciando Telethon con StringSession...")
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
else:
    print("📁 Usando sesión por archivo local (sesion_hugo)...")
    client = TelegramClient('sesion_hugo', API_ID, API_HASH)

chat_id_hugo = None
loop_principal = None

entidad_franchesco = None
entidad_ghostops   = None
entidad_north_bot  = None
entidad_liam_bot   = None
entidad_kimico     = None

id_franchesco = None
id_ghostops   = None
id_north_bot  = None
id_liam_bot   = None
id_kimico     = None

control_operaciones = {}
north_respondido_exito = {}
imagenes_procesadas_recientes = []

async def mapear_motores_por_id():
    global entidad_franchesco, entidad_ghostops, entidad_north_bot, entidad_liam_bot, entidad_kimico
    global id_franchesco, id_ghostops, id_north_bot, id_liam_bot, id_kimico

    if not client.is_connected():
        await client.connect()

    print("📋 Sincronizando e indexando IDs reales de Telegram...")
    GRUPOS_A_OBVIAR = ["CANAL FRANCHESCO DATA SAC", "FRANCHESCO MASTER", "DF VIP [ GRUPO 05 ]"]

    async for dialog in client.iter_dialogs(limit=150):
        if dialog.name:
            nombre_chat_upper = dialog.name.strip().upper()

            if any(obviar.upper() in nombre_chat_upper for obviar in GRUPOS_A_OBVIAR):
                continue

            if TXT_FRANCHESCO in nombre_chat_upper and not entidad_franchesco:
                entidad_franchesco = dialog.input_entity
                id_franchesco = dialog.id
                print(f"🎯 ID Franchesco Fijado: {id_franchesco} ({dialog.name})")

            elif TXT_GHOSTOPS in nombre_chat_upper and not entidad_ghostops:
                entidad_ghostops = dialog.input_entity
                id_ghostops = dialog.id
                print(f"🎯 ID DF VIP [GRUPO 08] Fijado: {id_ghostops} ({dialog.name})")

            # --- KIMICO PAUSADO TEMPORALMENTE ---
            # elif "KIMICO" in nombre_chat_upper and "BOT" in nombre_chat_upper and not entidad_kimico:
            #     entidad_kimico = dialog.input_entity
            #     id_kimico = dialog.id
            #     print(f"🎯 ID KIMICO BOT Fijado: {id_kimico} ({dialog.name})")

    try:
        entidad_north_bot = await client.get_input_entity(USER_NORTH_BOT)
        full_north = await client.get_entity(entidad_north_bot)
        id_north_bot = full_north.id
        print(f"🎯 ID North Bot Fijado: {id_north_bot} (@{USER_NORTH_BOT})")
    except Exception as e:
        print(f"⚠️ Alerta North Bot: {e}")

    try:
        entidad_liam_bot = await client.get_input_entity(USER_LIAM_BOT)
        full_liam = await client.get_entity(entidad_liam_bot)
        id_liam_bot = full_liam.id
        print(f"🎯 ID Liam Bot Fijado: {id_liam_bot} (@{USER_LIAM_BOT})")
    except Exception as e:
        print(f"⚠️ Alerta Liam: {e}")

async def flujo_especial_north(placa, clave_operacion):
    global entidad_north_bot, north_respondido_exito, control_operaciones
    if not entidad_north_bot: return

    north_respondido_exito[clave_operacion] = False
    print(f"⏱️ [NORTH DATA] Enviando primer paso /tiv {placa} para {clave_operacion}")
    try:
        await client.send_message(entidad_north_bot, f"/tiv {placa}")
    except Exception as e:
        print(f"❌ Error al enviar /tiv a North: {e}")

    await asyncio.sleep(30)

    if clave_operacion in control_operaciones:
        print(f"🔄 [NORTH DATA] Pasaron 30s. Ejecutando segundo paso con /tive {placa}")
        try:
            await client.send_message(entidad_north_bot, f"/tive {placa}")
        except Exception as e:
            print(f"❌ Error en envío de /tive a North: {e}")

def liberar_operacion_de_memoria(clave_operacion):
    global control_operaciones, north_respondido_exito
    if clave_operacion in control_operaciones:
        msg_carga = control_operaciones[clave_operacion].get("msg_carga")
        if msg_carga:
            try:
                bot.delete_message(msg_carga.chat.id, msg_carga.message_id)
            except Exception:
                pass
        del control_operaciones[clave_operacion]
        print(f"🧹 [MEMORIA] Operación [{clave_operacion}] liberada.")

    if clave_operacion in north_respondido_exito:
        del north_respondido_exito[clave_operacion]

async def timeout_seguridad_operacion(clave_operacion, segundos=90):
    await asyncio.sleep(segundos)
    global control_operaciones
    if clave_operacion in control_operaciones:
        print(f"⏱️ [TIME-OUT] Forzando liberación de [{clave_operacion}] ({segundos}s).")
        liberar_operacion_de_memoria(clave_operacion)

def verificar_y_marcar_respuesta(clave_operacion, motor):
    global control_operaciones
    if clave_operacion not in control_operaciones:
        return

    if motor in control_operaciones[clave_operacion]["motores"]:
        control_operaciones[clave_operacion]["motores"][motor] = True
        print(f"📊 [PROGRESO {clave_operacion}]: {motor} -> ✅ REGISTRADO.")

    if all(control_operaciones[clave_operacion]["motores"].values()):
        liberar_operacion_de_memoria(clave_operacion)

# =====================================================================
# --- SECCIÓN DE COMANDOS ---
# =====================================================================

@bot.message_handler(commands=['partida'])
def recibir_orden_docs(message):
    global chat_id_hugo, entidad_ghostops, loop_principal, control_operaciones
    chat_id_hugo = message.chat.id
    texto = message.text.split()
    if len(texto) < 2:
        bot.reply_to(message, "❌ Envía la placa o partida. Ejemplo: /partida CAJ270")
        return

    placa = texto[1].upper().strip().replace("-", "").replace(" ", "")
    clave_operacion = f"{placa}_PARTIDA"

    if entidad_ghostops:
        msg_carga = bot.reply_to(message, f"🔍 Consultando PDF para {placa} en DF VIP...")
        control_operaciones[clave_operacion] = {
            "placa": placa,
            "origen": "PARTIDA",
            "msg_carga": msg_carga,
            "motores": {"DF VIP": False}
        }
        if loop_principal:
            asyncio.run_coroutine_threadsafe(client.send_message(entidad_ghostops, f"/PARTIDAV {placa}"), loop_principal)
            asyncio.run_coroutine_threadsafe(timeout_seguridad_operacion(clave_operacion, 90), loop_principal)

@bot.message_handler(commands=['placa'])
def recibir_orden_imagenes(message):
    global chat_id_hugo, entidad_north_bot, loop_principal, control_operaciones
    chat_id_hugo = message.chat.id
    texto = message.text.split()
    if len(texto) < 2:
        bot.reply_to(message, "❌ Envía la placa. Ejemplo: /placa CAJ270")
        return

    placa = texto[1].upper().strip().replace("-", "").replace(" ", "")
    clave_operacion = f"{placa}_PLACA"

    if entidad_north_bot:
        msg_carga = bot.reply_to(message, f"📸 Consultando en NORTH DATA para {placa}...")
        control_operaciones[clave_operacion] = {
            "placa": placa,
            "origen": "PLACA",
            "msg_carga": msg_carga,
            "fotos_north": 0,
            "motores": {"NORTH DATA": False}
        }
        if loop_principal:
            asyncio.run_coroutine_threadsafe(client.send_message(entidad_north_bot, f"/pla {placa}"), loop_principal)
            asyncio.run_coroutine_threadsafe(timeout_seguridad_operacion(clave_operacion, 90), loop_principal)

@bot.message_handler(commands=['tive'])
def recibir_orden_tive_global(message):
    global chat_id_hugo, loop_principal, control_operaciones
    global entidad_ghostops, entidad_franchesco, entidad_north_bot, entidad_liam_bot, entidad_kimico

    chat_id_hugo = message.chat.id
    texto = message.text.split()
    if len(texto) < 2:
        bot.reply_to(message, "❌ Envía la placa. Ejemplo: /tive CAJ270")
        return

    placa = texto[1].upper().strip().replace("-", "").replace(" ", "")
    clave_operacion = f"{placa}_TIVE"
    msg_carga = bot.reply_to(message, f"⚡ ¡Ráfaga /tive activada para {placa}!\nDisparando consultas a los proveedores...")

    if not loop_principal: return
    control_operaciones[clave_operacion] = {
        "placa": placa,
        "origen": "TIVE",
        "msg_carga": msg_carga,
        "fotos_north": 0,
        "motores": {
            "DF VIP": False,
            "FRANCHESCO": False,
            "NORTH DATA": False,
            "LIAM DATA": False
            # "KIMICO": False  <-- [PAUSADO]
        }
    }

    if entidad_franchesco:
        asyncio.run_coroutine_threadsafe(client.send_message(entidad_franchesco, f"/tive {placa}"), loop_principal)
    if entidad_ghostops:
        asyncio.run_coroutine_threadsafe(client.send_message(entidad_ghostops, f"/tive {placa}"), loop_principal)
    
    # --- KIMICO PAUSADO TEMPORALMENTE ---
    # if entidad_kimico:
    #     asyncio.run_coroutine_threadsafe(client.send_message(entidad_kimico, f"/pla {placa}"), loop_principal)
    
    if entidad_north_bot:
        asyncio.run_coroutine_threadsafe(flujo_especial_north(placa, clave_operacion), loop_principal)

    asyncio.run_coroutine_threadsafe(timeout_seguridad_operacion(clave_operacion, 90), loop_principal)

@bot.message_handler(commands=['boleta'])
def recibir_orden_boleta_global(message):
    global chat_id_hugo, loop_principal, control_operaciones
    global entidad_ghostops, entidad_franchesco, entidad_north_bot, entidad_liam_bot, entidad_kimico

    chat_id_hugo = message.chat.id
    texto = message.text.split()
    if len(texto) < 2:
        bot.reply_to(message, "❌ Envía la placa. Ejemplo: /boleta CAJ270")
        return

    placa = texto[1].upper().strip().replace("-", "").replace(" ", "")
    clave_operacion = f"{placa}_BOLETA"
    msg_carga = None
    try:
        msg_carga = bot.reply_to(message, f"🧾 ¡Ráfaga /boleta activada para {placa}!\nDisparando consultas de boletas informativas...")
    except Exception as network_error:
        print(f"⚠️ Aviso de red: {network_error}")

    if not loop_principal: return
    control_operaciones[clave_operacion] = {
        "placa": placa,
        "origen": "BOLETA",
        "msg_carga": msg_carga,
        "motores": {
            "DF VIP": False,
            "FRANCHESCO": False,
            "NORTH DATA": False,
            "LIAM DATA": False
            # "KIMICO": False  <-- [PAUSADO]
        }
    }

    if entidad_franchesco:
        asyncio.run_coroutine_threadsafe(client.send_message(entidad_franchesco, f"/boi {placa}"), loop_principal)
    if entidad_ghostops:
        asyncio.run_coroutine_threadsafe(client.send_message(entidad_ghostops, f"/boi {placa}"), loop_principal)
    
    # --- KIMICO PAUSADO TEMPORALMENTE ---
    # if entidad_kimico:
    #     asyncio.run_coroutine_threadsafe(client.send_message(entidad_kimico, f"/boleta {placa}"), loop_principal)
    
    if entidad_north_bot:
        asyncio.run_coroutine_threadsafe(client.send_message(entidad_north_bot, f"/bolif {placa}"), loop_principal)

    asyncio.run_coroutine_threadsafe(timeout_seguridad_operacion(clave_operacion, 90), loop_principal)

@bot.message_handler(commands=['propiedades'])
def recibir_orden_partidadni_global(message):
    global chat_id_hugo, loop_principal, control_operaciones
    global entidad_ghostops, entidad_franchesco

    chat_id_hugo = message.chat.id
    texto = message.text.split()
    if len(texto) < 2:
        bot.reply_to(message, "❌ Envía el DNI. Ejemplo: /propiedades 12345678")
        return

    dni = texto[1].upper().strip()
    clave_operacion = f"{dni}_PARTIDADNI"
    msg_carga = None
    try:
        msg_carga = bot.reply_to(message, f"📑 ¡Ráfaga /propiedades activada para DNI: {dni}!\nConsultando...")
    except Exception as network_error:
        print(f"⚠️ Aviso de red: {network_error}")

    if not loop_principal: return
    control_operaciones[clave_operacion] = {
        "placa": dni,
        "origen": "PARTIDADNI",
        "msg_carga": msg_carga,
        "motores": {
            "DF VIP": False,
            "FRANCHESCO": False
        }
    }

    if entidad_franchesco:
        asyncio.run_coroutine_threadsafe(client.send_message(entidad_franchesco, f"/propdf {dni}"), loop_principal)
    if entidad_ghostops:
        asyncio.run_coroutine_threadsafe(client.send_message(entidad_ghostops, f"/propdf {dni}"), loop_principal)

    asyncio.run_coroutine_threadsafe(timeout_seguridad_operacion(clave_operacion, 90), loop_principal)

@bot.message_handler(commands=['nombre'])
def recibir_orden_nombre_global(message):
    global chat_id_hugo, loop_principal, control_operaciones
    global entidad_ghostops, entidad_franchesco

    chat_id_hugo = message.chat.id
    texto_completo = message.text.split(maxsplit=1)
    if len(texto_completo) < 2:
        bot.reply_to(message, "❌ Envía el nombre completo. Ejemplo: /nombre CRISTIAN CONDORI MONTOYA")
        return

    nombre_original = texto_completo[1].upper().strip()
    palabras = nombre_original.split()
    nombre_formateado = " | ".join(palabras)
    clave_operacion = f"{''.join(palabras)}_NOMBRE"

    msg_carga = None
    try:
        msg_carga = bot.reply_to(message, f"👤 Búsqueda por Nombre activada: {nombre_original}\nFormato: `/nm {nombre_formateado}`")
    except Exception as network_error:
        print(f"⚠️ Aviso de red: {network_error}")

    if not loop_principal: return
    control_operaciones[clave_operacion] = {
        "placa": "".join(palabras),
        "origen": "NOMBRE",
        "msg_carga": msg_carga,
        "motores": {
            "DF VIP": False,
            "FRANCHESCO": False
        }
    }

    if entidad_franchesco:
        asyncio.run_coroutine_threadsafe(client.send_message(entidad_franchesco, f"/nm {nombre_formateado}"), loop_principal)
    if entidad_ghostops:
        asyncio.run_coroutine_threadsafe(client.send_message(entidad_ghostops, f"/nm {nombre_formateado}"), loop_principal)

    asyncio.run_coroutine_threadsafe(timeout_seguridad_operacion(clave_operacion, 90), loop_principal)

@bot.message_handler(commands=['denuncias'])
def recibir_orden_denuncias_global(message):
    global chat_id_hugo, loop_principal, control_operaciones
    global entidad_ghostops, entidad_franchesco

    chat_id_hugo = message.chat.id
    texto = message.text.split()
    if len(texto) < 2:
        bot.reply_to(message, "❌ Envía la placa. Ejemplo: /denuncias CAJ270")
        return

    placa = texto[1].upper().strip().replace("-", "").replace(" ", "")
    clave_operacion = f"{placa}_DENUNCIAS"
    msg_carga = None
    try:
        msg_carga = bot.reply_to(message, f"🚨 ¡Ráfaga /denuncias activada para {placa}!\nConsultando antecedentes...")
    except Exception as network_error:
        print(f"⚠️ Aviso de red: {network_error}")

    if not loop_principal: return
    control_operaciones[clave_operacion] = {
        "placa": placa,
        "origen": "DENUNCIAS",
        "msg_carga": msg_carga,
        "motores": {
            "DF VIP": False,
            "FRANCHESCO": False
        }
    }

    if entidad_franchesco:
        asyncio.run_coroutine_threadsafe(client.send_message(entidad_franchesco, f"/denpla {placa}"), loop_principal)
    if entidad_ghostops:
        asyncio.run_coroutine_threadsafe(client.send_message(entidad_ghostops, f"/denunv {placa}"), loop_principal)

    asyncio.run_coroutine_threadsafe(timeout_seguridad_operacion(clave_operacion, 90), loop_principal)

@bot.message_handler(commands=['rq'])
def recibir_orden_rq_global(message):
    global chat_id_hugo, loop_principal, control_operaciones
    global entidad_north_bot, entidad_kimico

    chat_id_hugo = message.chat.id
    texto = message.text.split()
    if len(texto) < 2:
        bot.reply_to(message, "❌ Envía la placa. Ejemplo: /rq CAJ270")
        return

    placa = texto[1].upper().strip().replace("-", "").replace(" ", "")
    clave_operacion = f"{placa}_RQ"
    msg_carga = None
    try:
        msg_carga = bot.reply_to(message, f"🔍 ¡Consulta /rq activada para {placa}!\nDisparando solicitud...")
    except Exception as network_error:
        print(f"⚠️ Aviso de red: {network_error}")

    if not loop_principal: return
    control_operaciones[clave_operacion] = {
        "placa": placa,
        "origen": "RQ",
        "msg_carga": msg_carga,
        "motores": {
            "NORTH DATA": False
            # "KIMICO": False  <-- [PAUSADO]
        }
    }

    if entidad_north_bot:
        asyncio.run_coroutine_threadsafe(client.send_message(entidad_north_bot, f"/rqpla {placa}"), loop_principal)
    
    # --- KIMICO PAUSADO TEMPORALMENTE ---
    # if entidad_kimico:
    #     asyncio.run_coroutine_threadsafe(client.send_message(entidad_kimico, f"/rqpla {placa}"), loop_principal)

    asyncio.run_coroutine_threadsafe(timeout_seguridad_operacion(clave_operacion, 90), loop_principal)

# =====================================================================
# --- PANEL INTERACTIVO Y MENÚ ---
# =====================================================================

def generar_menu_principal(first_name):
    markup = InlineKeyboardMarkup(row_width=2)
    numero_whatsapp = "51952513161"

    msg_ayuda = urllib.parse.quote("NECESITO AYUDA POR FAVOR LLAMAME")
    msg_avisar = urllib.parse.quote("hay algo que no esta funcionando bien")
    msg_urgencia = urllib.parse.quote("por favor llamame urgente tengo unos problemas")

    btn_ayuda = InlineKeyboardButton("🆘 AYUDA", url=f"https://wa.me/{numero_whatsapp}?text={msg_ayuda}")
    btn_avisar = InlineKeyboardButton("📢 AVISAR", url=f"https://wa.me/{numero_whatsapp}?text={msg_avisar}")
    btn_urgencia = InlineKeyboardButton("🚨 URGENCIA", url=f"https://wa.me/{numero_whatsapp}?text={msg_urgencia}")
    btn_vehiculos = InlineKeyboardButton("🚙 VEHICULOS", callback_data="menu_vehiculos")

    markup.add(btn_vehiculos, btn_ayuda)
    markup.add(btn_avisar, btn_urgencia)

    texto = (
        f"Hola, <b>{first_name}</b>\n\n"
        "💻 <b>[ PANEL DE COMANDOS ]</b>\n\n"
        "Bienvenido a este <b>BOT VEHICULAR</b> de uso exclusivo.\n\n"
        "<b>Selecciona una opción según la categoría que deseas explorar.</b>\n"
    )
    return texto, markup

@bot.message_handler(commands=['start', 'menu', 'cmds'])
def enviar_panel_comandos(message):
    texto, markup = generar_menu_principal(message.from_user.first_name)
    bot.send_message(message.chat.id, texto, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def responder_clicks_botones(call):
    if call.data == "menu_vehiculos":
        markup_vehiculos = InlineKeyboardMarkup()
        btn_regresar = InlineKeyboardButton("⬅️ Volver al Menú", callback_data="volver_principal")
        markup_vehiculos.add(btn_regresar)

        texto_vehiculos = (
            "📋 <b>[ CATEGORÍA ⇒ VEHÍCULOS ]</b>\n\n"
            "1️⃣ <b>CONSULTA PARTIDA DEL VEHICULO (DF VIP)</b>\n"
            "• Comando: /partida [placa]\n"
            "• Ejemplo: /partida CAJ270\n\n"
            "2️⃣ <b>CONSULTA PLACA (FRANCHESCO)</b>\n"
            "• Comando: /placa [placa]\n"
            "• Ejemplo: /placa CAJ270\n\n"
            "3️⃣ <b>BUSQUEDA TIVE EN BOTS</b>\n"
            "• Comando: /tive [placa]\n"
            "• Ejemplo: /tive CAJ270\n\n"
            "4️⃣ <b>BUSQUEDA BOLETAS INFORMATIVAS</b>\n"
            "• Comando: /boleta [placa]\n"
            "• Ejemplo: /boleta CAJ270\n\n"
            "5️⃣ <b>BUSQUEDA DENUNCIAS DEL VEHICULO</b>\n"
            "• Comando: /denuncias [placa]\n"
            "• Ejemplo: /denuncias CAJ270\n\n"
            "6️⃣ <b>BUSCA TODAS LAS PROPIEDADES POR DNI</b>\n"
            "• Comando: /propiedades [DNI]\n"
            "• Ejemplo: /propiedades 44556677\n\n"
            "7️⃣ <b>BUSCA EL DNI POR NOMBRE</b>\n"
            "• Comando: /nombre [NOMBRE Y APELLIDO]\n"
            "• Ejemplo: /nombre Cristian Condori Montoya\n\n"
            "8️⃣ <b>CONSULTA REQUERIMIENTO (RQ)</b>\n"
            "• Comando: /rq [placa]\n"
            "• Ejemplo: /rq CAJ270"
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=texto_vehiculos, parse_mode="HTML", reply_markup=markup_vehiculos)

    elif call.data == "volver_principal":
        bot.answer_callback_query(call.id)
        texto_menu, markup_menu = generar_menu_principal(call.from_user.first_name)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=texto_menu,
            parse_mode="HTML",
            reply_markup=markup_menu
        )

    elif call.data.startswith("prov_"):
        partes = call.data.split("_")
        if len(partes) < 4: return

        prov_chat_id = int(partes[1])
        prov_msg_id = int(partes[2])
        boton_data_hex = partes[3]
        boton_data_bytes = bytes.fromhex(boton_data_hex)

        bot.answer_callback_query(call.id, text="⏳ Solicitando documento al proveedor...")

        if loop_principal:
            async def presionar_boton_remoto():
                try:
                    mensaje_remoto = await client.get_messages(prov_chat_id, ids=prov_msg_id)
                    if mensaje_remoto and mensaje_remoto.reply_markup:
                        for i, row in enumerate(mensaje_remoto.reply_markup.rows):
                            for j, button in enumerate(row.buttons):
                                if hasattr(button, 'data') and button.data == boton_data_bytes:
                                    print(f"⚡ Pulsando botón '{button.text}'...")
                                    await mensaje_remoto.click(i, j)
                                    return
                except Exception as e:
                    print(f"❌ Error al presionar botón proveedor: {e}")

            asyncio.run_coroutine_threadsafe(presionar_boton_remoto(), loop_principal)

def arrancar_bot_padre():
    try:
        bot.remove_webhook()
    except Exception as e:
        print(f"⚠️ Aviso Webhook: {e}")

    while True:
        try:
            print("🤖 Servidor Telebot iniciando polling...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60, logger_level=50)
        except Exception as e:
            error_msg = str(e)
            if "Conflict" in error_msg or "409" in error_msg:
                print("⏳ Conflicto 409 detectado (reinicio previo). Reintentando en 8 segundos...")
                time.sleep(8)
            else:
                print(f"❌ Error en Telebot: {e}. Reiniciando en 5s...")
                time.sleep(5)

# --- CLIENTE ASÍNCRONO TELETHON ---
async def main():
    global loop_principal, control_operaciones, north_respondido_exito
    global id_franchesco, id_ghostops, id_north_bot, id_liam_bot, id_kimico
    loop_principal = asyncio.get_running_loop()

    await mapear_motores_por_id()

    @client.on(events.NewMessage())
    async def escuchador_global_mensajes(event):
        global chat_id_hugo, control_operaciones, north_respondido_exito
        global id_franchesco, id_ghostops, id_north_bot, id_liam_bot, id_kimico

        chat_actual_id = event.chat_id
        if not chat_id_hugo or not control_operaciones:
            return

        origen_texto = "DESCONOCIDO"
        if id_franchesco and chat_actual_id == id_franchesco: origen_texto = "FRANCHESCO"
        elif id_ghostops and chat_actual_id == id_ghostops: origen_texto = "DF VIP"
        elif id_north_bot and chat_actual_id == id_north_bot: origen_texto = "NORTH DATA"
        elif id_liam_bot and chat_actual_id == id_liam_bot: origen_texto = "LIAM DATA"
        # elif id_kimico and chat_actual_id == id_kimico: origen_texto = "KIMICO"  # [PAUSADO]

        if origen_texto == "DESCONOCIDO": return

        op_encontrada = None
        placa_detectada = None
        texto_a_buscar = ""

        if event.message.text:
            texto_a_buscar = event.message.text.upper()
        if event.message.media and event.message.document:
            for attr in event.message.document.attributes:
                if hasattr(attr, 'file_name') and attr.file_name:
                    texto_a_buscar += " " + attr.file_name.upper()

        for clave, op_data in list(control_operaciones.items()):
            if op_data["placa"] in texto_a_buscar.replace("-", "").replace("_", "").replace(" ", "").replace("|", ""):
                if origen_texto in op_data["motores"]:
                    op_encontrada = clave
                    placa_detectada = op_data["placa"]
                    break

        if not op_encontrada:
            for clave, op_data in list(control_operaciones.items()):
                if origen_texto in op_data["motores"] and not op_data["motores"][origen_texto]:
                    if op_data["origen"] == "NOMBRE":
                        if texto_a_buscar.strip().startswith("/"):
                            continue
                        palabras_validas_nombre = ["DNI", "NOMBRES", "APELLIDOS", "RESULTADOS", "NO SE ENCONTRÓ", "NO SE ENCONTRO", "ERROR", "NO EXISTE", "ANTI-SPAM"]
                        if any(palabra in texto_a_buscar for palabra in palabras_validas_nombre):
                            op_encontrada = clave
                            placa_detectada = op_data["placa"]
                            break
                        else:
                            continue

                    if origen_texto in ["NORTH DATA", "LIAM DATA"]:
                        if op_data["origen"] in ["TIVE", "BOLETA", "RQ"]:
                            op_encontrada = clave
                            placa_detectada = op_data["placa"]
                            break
                    elif origen_texto == "DF VIP":
                        if op_data["origen"] in ["PARTIDA", "PARTIDAV", "PARTIDADNI"]:
                            if "MEXES" in texto_a_buscar or "PARTIDA" in texto_a_buscar:
                                op_encontrada = clave
                                placa_detectada = op_data["placa"]
                                break
                    elif origen_texto == "FRANCHESCO":
                        palabras_validas_franchesco = ["MEXES", "HUGO", "BOLETA", "TIVE", "INFORMATIVA", "PROCESADO", "REGISTRO", "NO SE ENCONTRÓ", "NO SE ENCONTRO", "ERROR", "NO EXISTE", "SIN RESULTADOS"]
                        if any(palabra in texto_a_buscar for palabra in palabras_validas_franchesco):
                            op_encontrada = clave
                            placa_detectada = op_data["placa"]
                            break

        if not op_encontrada:
            return

        # Entrega de Documentos (PDF)
        if event.message.media and event.message.document:
            nombre_original = "documento.pdf"
            for attr in event.message.document.attributes:
                if hasattr(attr, 'file_name') and attr.file_name:
                    nombre_original = attr.file_name
                    break

            if origen_texto == "NORTH DATA":
                north_respondido_exito[op_encontrada] = True

            ruta = await event.message.download_media(file=nombre_original)
            tipo_identificador = "👤 DNI" if control_operaciones[op_encontrada]["origen"] == "PARTIDADNI" else "🏁 Placa/Partida"
            caption_personalizado = f"📄 <b>Resultado ({origen_texto}):</b>\n{tipo_identificador}: <code>{placa_detectada}</code>"

            with open(ruta, 'rb') as doc:
                bot.send_document(chat_id_hugo, doc, caption=caption_personalizado, parse_mode="HTML")

            if os.path.exists(ruta):
                try: os.remove(ruta)
                except Exception: pass

            verificar_y_marcar_respuesta(op_encontrada, origen_texto)
            return

        # Entrega de Fotos
        elif event.message.media and event.message.photo and origen_texto in ["FRANCHESCO", "NORTH DATA"]:
            comando_origen = control_operaciones[op_encontrada]["origen"]
            caption_proveedor = event.message.message if event.message.message else ""

            palabras_carga_imagen = ["CONSULTANDO PLACA", "POR FAVOR ESPERA", "ESTAMOS PROCESANDO", "UN MOMENTO PORFAVOR", "UN MOMENTO POR FAVOR", "PROCESANDO TU SOLICITUD"]
            if any(carga in caption_proveedor.upper() for carga in palabras_carga_imagen):
                return

            if origen_texto == "NORTH DATA" and comando_origen == "TIVE":
                return

            if origen_texto == "FRANCHESCO" and comando_origen in ["TIVE", "BOLETA", "DENUNCIAS"]:
                verificar_y_marcar_respuesta(op_encontrada, "FRANCHESCO")
                return

            ruta_img = await event.message.download_media(file=f"{placa_detectada}.jpg")
            try:
                msg_carga = control_operaciones[op_encontrada].get("msg_carga")
                if msg_carga:
                    try: bot.delete_message(msg_carga.chat.id, msg_carga.message_id)
                    except Exception: pass

                with open(ruta_img, 'rb') as foto_enviar:
                    bot.send_photo(chat_id_hugo, foto_enviar)
            except Exception as e:
                print(f"❌ Error al enviar foto: {e}")

            verificar_y_marcar_respuesta(op_encontrada, origen_texto)
            if os.path.exists(ruta_img):
                try: os.remove(ruta_img)
                except Exception: pass
            return

        # Entrega de Texto
        elif event.message.text:
            texto_grupo = event.message.text.upper()

            if texto_grupo.startswith(('/TIVE', '/TIV', '/PLA', '/PARTI', '/BOI', '/BOLI', '/BOLETA', '/DENPLA', '/DENUNV', '/PROP')) and len(texto_grupo) < 15 and "NO SE" not in texto_grupo:
                return

            if texto_grupo.strip() == "CMDS" or (texto_grupo.startswith('/') and len(texto_grupo) < 7):
                return

            if origen_texto == "FRANCHESCO" and "ANTI-SPAM ACTIVADO" in texto_grupo:
                bot.send_message(chat_id_hugo, f"⏳ <b>Alerta [{origen_texto}]:</b>\n\n⚠️ Anti-Spam activo en este proveedor. Espera unos segundos.", parse_mode="HTML")
                verificar_y_marcar_respuesta(op_encontrada, "FRANCHESCO")
                return

            palabras_carga = ["BUSCANDO", "PROCESANDO", "ESPERE", "CONSULTANDO", "RECIBIDO", "UN MOMENTO", "BUSQUEDA ACTIVADA", "SOLICITUD RECIBIDA", "CRÉDITOS RESTANTES", "OBTENIENDO LA TIVE", "OBTENIENDO"]
            if any(carga in texto_grupo for carga in palabras_carga):
                return

            comando_origen = control_operaciones[op_encontrada]["origen"]

            if origen_texto == "FRANCHESCO":
                if any(err in texto_grupo for err in ["NO SE ENCONTRÓ", "NO SE ENCONTRO", "ERROR"]):
                    if comando_origen in ["PLACA", "DENUNCIAS"]:
                        msg_carga = control_operaciones[op_encontrada].get("msg_carga")
                        if msg_carga:
                            try: bot.delete_message(msg_carga.chat.id, msg_carga.message_id)
                            except Exception: pass

                    bot.send_message(chat_id_hugo, f"📢 <b>Respuesta de [{origen_texto}]:</b>\n🏁 Placa/Partida: <code>{placa_detectada}</code>\n\n❌ No se encontró información.", parse_mode="HTML")
                    verificar_y_marcar_respuesta(op_encontrada, origen_texto)
                    return

            if origen_texto == "DF VIP":
                es_error_df = any(err in texto_grupo for err in ["NO SE ENCONTRÓ", "NO SE ENCONTRO", "ERROR", "NO EXISTE"])
                if es_error_df:
                    if comando_origen == "TIVE":
                        bot.send_message(chat_id_hugo, f"⚠️ <b>Aviso [DF VIP]:</b>\n🏁 Placa: <code>{placa_detectada}</code>\n\n❌ TIVE no encontrada. Consultando Partida en 15s...", parse_mode="HTML")

                        async def ejecutar_respaldo_partida(id_grupo, placa, clave_op):
                            await asyncio.sleep(15)
                            global control_operaciones
                            if clave_op in control_operaciones:
                                control_operaciones[clave_op]["origen"] = "PARTIDAV"
                                await client.send_message(id_grupo, f"/partidav {placa}")

                        asyncio.run_coroutine_threadsafe(ejecutar_respaldo_partida(id_ghostops, placa_detectada, op_encontrada), loop_principal)
                        return

                    if comando_origen in ["PARTIDAV", "DENUNCIAS", "PARTIDADNI"]:
                        msg_carga = control_operaciones[op_encontrada].get("msg_carga")
                        if msg_carga:
                            try: bot.delete_message(msg_carga.chat.id, msg_carga.message_id)
                            except Exception: pass

                    bot.send_message(chat_id_hugo, f"⚠️ <b>Resultado [{origen_texto}]:</b>\n🏁 Placa: <code>{placa_detectada}</code>\n\n❌ Sin registros disponibles.", parse_mode="HTML")
                    verificar_y_marcar_respuesta(op_encontrada, origen_texto)
                    return

                elif comando_origen == "PARTIDAV":
                    if "MEXES" not in texto_grupo and "PARTIDA" not in texto_grupo:
                        return

            if origen_texto == "NORTH DATA":
                es_error_north = any(err in texto_grupo for err in ["NO SE HAN ENCONTRADO DATOS", "NOT FOUND DATA", "NO SE ENCONTRÓ", "NO SE ENCONTRO", "NO SE HALLARON", "ERROR", "NO EXISTE", "NO CUENTA CON TIVE"])
                if es_error_north:
                    texto_original = event.message.text
                    reporte_recortado = "⚠️ Sin resultados o no cuenta con TIVE."
                    if "NO CUENTA CON TIVE" in texto_original.upper():
                        for linea in texto_original.split('\n'):
                            if "NO CUENTA CON TIVE" in linea.upper():
                                reporte_recortado = linea.strip()
                                break
                    else:
                        lineas = [l for l in texto_original.split('\n') if "CONSULTADO POR" not in l.upper() and "CREDITOS" not in l.upper()]
                        reporte_recortado = "\n".join(lineas).strip() or texto_original.strip()

                    bot.send_message(chat_id_hugo, f"📢 <b>Respuesta de [{origen_texto}]:</b>\n🏁 Placa/Partida: <code>{placa_detectada}</code>\n\n{reporte_recortado}", parse_mode="HTML")

                    if comando_origen == "TIVE" and not north_respondido_exito.get(op_encontrada):
                        pass
                    else:
                        verificar_y_marcar_respuesta(op_encontrada, origen_texto)
                    return
                else:
                    return

            texto_original = event.message.text
            lineas_limpias = []
            for linea in texto_original.split('\n'):
                if "CONSULTADO POR" in linea.upper() or "CREDITOS" in linea.upper(): break
                linea_procesada = linea.replace("`", "").replace("**", "").replace("__", "").replace("*", "").replace("[", "").replace("]", "")
                linea_procesada = re.sub(r'(=&gt;|&gt;|⇒|=>|->|➾)', ':', linea_procesada)
                lineas_limpias.append(linea_procesada)

            reporte_recortado = "\n".join(lineas_limpias).strip() or texto_original.strip()

            try:
                markup_botones = None
                if event.message.reply_markup and hasattr(event.message.reply_markup, 'rows'):
                    markup_botones = InlineKeyboardMarkup()
                    for row in event.message.reply_markup.rows:
                        fila_botones = []
                        for button in row.buttons:
                            if hasattr(button, 'data'):
                                boton_data_hex = button.data.hex()
                                callback_compuesto = f"prov_{chat_actual_id}_{event.message.id}_{boton_data_hex}"
                                if len(callback_compuesto) <= 64:
                                    fila_botones.append(InlineKeyboardButton(text=button.text, callback_data=callback_compuesto))
                        if fila_botones:
                            markup_botones.add(*fila_botones)

                mensaje_html = f"📢 <b>Respuesta de [{origen_texto}]:</b>\n🏁 Placa/Partida: <code>{placa_detectada}</code>\n\n{reporte_recortado}"
                bot.send_message(chat_id_hugo, mensaje_html, parse_mode="HTML", reply_markup=markup_botones)
            except Exception as e:
                print(f"⚠️ Respaldo por excepción de formato: {e}")
                bot.send_message(chat_id_hugo, f"📢 Respuesta de [{origen_texto}]:\n🏁 Placa/Partida: {placa_detectada}\n\n{texto_original}")

            verificar_y_marcar_respuesta(op_encontrada, origen_texto)

    print("🚀 Sistema multimotor iniciado y en escucha.")
    await client.run_until_disconnected()

if __name__ == '__main__':
    threading.Thread(target=arrancar_bot_padre, daemon=True).start()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Bot detenido por el usuario.")
    finally:
        loop.close()