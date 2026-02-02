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

        # URL de descarga directa
        target_url = f"https://sinat.sat.gob.mx/CifDirecto/Home/Index?rfc={rfc}&idCif={idcif}"
        
        # Iniciamos una sesión para guardar cookies (esto es el truco clave)
        session = requests.Session()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,application/xhtml+xml,text/html;q=0.9,*/*;q=0.8',
            'Referer': 'https://www.sat.gob.mx/'
        }

        # Paso 1: "Tocamos la puerta" para obtener permiso (cookies)
        session.get("https://sinat.sat.gob.mx/CifDirecto/", headers=headers, timeout=15)

        # Paso 2: Pedimos el PDF con la sesión ya iniciada
        response = session.get(target_url, headers=headers, timeout=25)

        if response.status_code == 200 and b'%PDF' in response.content:
            return send_file(
                io.BytesIO(response.content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"CSF_{rfc}.pdf"
            )
            
        return jsonify({"message": "El SAT está saturado. Reintenta en 1 minuto."}), 404

    except Exception as e:
        return jsonify({"message": "Error de comunicación con el SAT."}), 500
        
