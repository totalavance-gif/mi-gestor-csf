from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import requests
import io
import urllib3

# Desactiva alertas de seguridad por el uso de IP y verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

        # CAMBIO CLAVE: Usamos http (sin S) e IP directa para saltar el error WRONG_VERSION_NUMBER
        url = f"http://200.57.3.46/CifDirecto/Home/Index?rfc={rfc}&idCif={idcif}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Host': 'sinat.sat.gob.mx'
        }
        
        # Realizamos la petición al servidor del SAT
        response = requests.get(url, headers=headers, timeout=25, verify=False)

        if response.status_code == 200 and b'%PDF' in response.content:
            return send_file(
                io.BytesIO(response.content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"CSF_{rfc}.pdf"
            )
            
        return jsonify({"message": "El SAT no generó el PDF. Verifica RFC e idCIF."}), 404

    except Exception as e:
        # Enviamos el error limpio a la interfaz
        return jsonify({"message": f"Error: {str(e)}"}), 500
        
