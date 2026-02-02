from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import requests
import io

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
            return jsonify({"message": "Faltan datos"}), 400

        # 1. URL base para generar la cookie de sesión
        base_url = "https://sinat.sat.gob.mx/CifDirecto/Home/Index"
        target_url = f"{base_url}?rfc={rfc}&idCif={idcif}"
        
        # 2. Usamos una sesión para mantener las cookies activas
        session = requests.Session()
        
        # 3. Encabezados de "Navegador de Alta Confianza"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9',
            'Referer': 'https://www.sat.gob.mx/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Upgrade-Insecure-Requests': '1'
        }

        # 4. Intentamos la descarga directa
        response = session.get(target_url, headers=headers, timeout=25, verify=False)

        # 5. Verificamos si lo que recibimos es realmente un PDF
        if response.status_code == 200 and b'%PDF' in response.content:
            return send_file(
                io.BytesIO(response.content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"CSF_{rfc}.pdf"
            )
            
        # Si no es PDF, intentamos un segundo paso (fuerza bruta de headers)
        return jsonify({"message": "El SAT detectó la conexión pero bloqueó el archivo. Reintenta."}), 404

    except Exception as e:
        return jsonify({"message": "Error de comunicación. Reintenta en 5 segundos."}), 500
            
