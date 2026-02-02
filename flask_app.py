from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import requests
import io
import urllib3

# Desactivar advertencias de seguridad por usar la IP directa y verify=False
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

        # Usamos la IP directa del SAT para evitar el NameResolutionError
        # IP: 200.57.3.46 corresponde a sinat.sat.gob.mx
        url = f"https://200.57.3.46/CifDirecto/Home/Index?rfc={rfc}&idCif={idcif}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Host': 'sinat.sat.gob.mx' # Forzamos el host en la cabecera
        }
        
        # timeout=25 para dar tiempo al SAT de responder
        # verify=False es obligatorio al usar la IP directa
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
        return jsonify({"message": f"Error de conexión: {str(e)}"}), 500

# Render no necesita app.run(), gunicorn se encarga

          
