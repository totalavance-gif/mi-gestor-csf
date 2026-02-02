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
        
        # Generamos una IP mexicana aleatoria para la máscara
        fake_ip = f"187.{random.randint(128,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

        # URL directa del PDF
        url = f"https://sinat.sat.gob.mx/CifDirecto/Home/Index?rfc={rfc}&idCif={idcif}"
        
        # Esta es la máscara técnica (Headers de Enmascaramiento)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'X-Forwarded-For': fake_ip,  # Aquí fingimos la IP
            'Client-IP': fake_ip,         # Otra capa de máscara
            'X-Real-IP': fake_ip,         # Y una más por si acaso
            'Referer': 'https://www.sat.gob.mx/',
            'Accept-Language': 'es-MX,es;q=0.9',
            'Connection': 'close'
        }

        # Petición al SAT con la máscara puesta
        # 'stream=True' para que la descarga sea más fluida y no pese en Vercel
        response = requests.get(url, headers=headers, timeout=20, verify=False, stream=True)

        if response.status_code == 200 and b'%PDF' in response.content:
            return send_file(
                io.BytesIO(response.content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"CSF_{rfc}.pdf"
            )
            
        return jsonify({"message": "El SAT detectó la conexión pero negó el archivo. Intenta de nuevo."}), 404

    except Exception as e:
        return jsonify({"message": "Error de enlace enmascarado. Reintenta."}), 500
            
