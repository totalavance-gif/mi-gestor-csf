from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import requests
import io
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

        # Regresamos al dominio oficial pero con gestión de reintentos
        url = f"https://sinat.sat.gob.mx/CifDirecto/Home/Index?rfc={rfc}&idCif={idcif}"
        
        session = requests.Session()
        # Configuramos 3 reintentos automáticos si falla la conexión
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,application/xhtml+xml,text/html;q=0.9',
            'Connection': 'keep-alive'
        }
        
        # Aumentamos el tiempo de espera a 30 segundos
        response = session.get(url, headers=headers, timeout=30, verify=True)

        if response.status_code == 200 and b'%PDF' in response.content:
            return send_file(
                io.BytesIO(response.content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"CSF_{rfc}.pdf"
            )
            
        return jsonify({"message": "El SAT no devolvió un PDF válido. Revisa tus datos."}), 404

    except Exception as e:
        return jsonify({"message": f"Error del servidor SAT: {str(e)}"}), 500
        
