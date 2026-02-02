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

        # URL del SAT
        target_url = f"https://sinat.sat.gob.mx/CifDirecto/Home/Index?rfc={rfc}&idCif={idcif}"
        
        # USAMOS UN PROXY (TÚNEL) PARA EVITAR EL NAMERESOLUTIONERROR
        # Este servidor externo sí puede ver al SAT y nos servirá de puente
        proxy_url = f"https://api.allorigins.win/raw?url={target_url}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/pdf'
        }

        # Pedimos el PDF a través del túnel
        response = requests.get(proxy_url, headers=headers, timeout=30)

        if response.status_code == 200 and b'%PDF' in response.content:
            return send_file(
                io.BytesIO(response.content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"CSF_{rfc}.pdf"
            )
            
        return jsonify({"message": "El SAT no respondió. Intenta de nuevo en unos segundos."}), 404

    except Exception as e:
        return jsonify({"message": f"Error de conexión: {str(e)}"}), 500
       
