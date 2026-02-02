from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import requests
import io
import random

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def generar():
    try:
        rfc = request.form.get('rfc', '').upper().strip()
        idcif = request.form.get('idcif', '').strip()
        
        if not rfc or not idcif:
            return jsonify({"message": "Datos incompletos"}), 400

        # ESTRATEGIA DE BYPASS 2026:
        # El SAT bloquea IPs de centros de datos. Usamos una IP aleatoria de México
        # en las cabeceras para simular un origen residencial (Infinitum/Totalplay).
        mexico_ip = f"187.{random.randint(128,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        
        url = f"https://sinat.sat.gob.mx/CifDirecto/Home/Index?rfc={rfc}&idCif={idcif}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,application/xhtml+xml,text/html;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9',
            'X-Forwarded-For': mexico_ip, # BYPASS: Máscara de IP mexicana
            'Client-IP': mexico_ip,        # BYPASS: Refuerzo de máscara
            'Referer': 'https://www.sat.gob.mx/consultas/31014/imprime-tu-cedula-de-identificacion-fiscal',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Dest': 'document',
            'Connection': 'close'
        }

        # Realizamos la petición. 'stream=True' evita que Vercel mate la función por peso.
        response = requests.get(url, headers=headers, timeout=25, verify=False, stream=True)

        # Si el SAT responde con un PDF (aunque digan que el endpoint no funciona, lo hace)
        if response.status_code == 200 and b'%PDF' in response.content:
            return send_file(
                io.BytesIO(response.content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"CSF_{rfc}.pdf"
            )
        
        # Si llegamos aquí, el bypass fue detectado por la IP de Vercel
        return jsonify({"message": "Bypass detectado por el SAT. Reintenta en 3 segundos."}), 403

    except Exception as e:
        print(f"Error en bypass: {str(e)}")
        return jsonify({"message": "Error de comunicación Ninja. Reintenta."}), 500
        
