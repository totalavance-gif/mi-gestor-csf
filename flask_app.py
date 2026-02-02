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
        
        # URL del recurso (mantenemos el CifDirecto pero con identidad técnica)
        url = f"https://sinat.sat.gob.mx/CifDirecto/Home/Index?rfc={rfc}&idCif={idcif}"
        
        # --- BYPASS DE IDENTIDAD TÉCNICA (Basado en tu captura) ---
        # Dejamos de fingir ser un navegador Chrome y fingimos ser el sistema
        # de comunicación de la imagen: Apache-HttpClient/4.1.1 (java 1.5)
        headers = {
            'User-Agent': 'Apache-HttpClient/4.1.1 (java 1.5)',
            'Accept-Encoding': 'gzip,deflate',
            'Accept': 'application/pdf, text/xml, */*',
            'Connection': 'Keep-Alive',
            'Host': 'sinat.sat.gob.mx',
            'Referer': 'https://www.sat.gob.mx/'
        }

        # Petición al SAT usando la identidad técnica
        response = requests.get(url, headers=headers, timeout=30, verify=False, stream=True)

        if response.status_code == 200 and b'%PDF' in response.content:
            return send_file(
                io.BytesIO(response.content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"CSF_{rfc}.pdf"
            )
        
        # Si el SAT responde pero pide el Token WRAP de tu imagen
        return jsonify({"message": "El SAT exige autenticación SOAP/WRAP. Bypass denegado."}), 401

    except Exception as e:
        return jsonify({"message": "Falla en protocolo de identidad técnica."}), 500
        
