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
    rfc = request.form.get('rfc', '').upper().strip()
    idcif = request.form.get('idcif', '').strip()
    
    # Iniciamos el agente efímero (muere al terminar este bloque)
    with requests.Session() as s:
        s.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Accept': 'application/pdf,application/xhtml+xml,text/html;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Referer': 'https://www.sat.gob.mx/',
            'Connection': 'close' # Le avisamos al SAT que cerraremos la conexión de inmediato
        })

        try:
            # Pedimos el PDF directamente para no dar vueltas innecesarias
            url = f"https://sinat.sat.gob.mx/CifDirecto/Home/Index?rfc={rfc}&idCif={idcif}"
            res = s.get(url, timeout=25, verify=False)

            if res.status_code == 200 and b'%PDF' in res.content:
                return send_file(
                    io.BytesIO(res.content),
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f"CSF_{rfc}.pdf"
                )
            
            return jsonify({"message": "El SAT rechazó el rastro. Intenta de nuevo."}), 404
        except Exception:
            return jsonify({"message": "Error de red efímera. Reintenta."}), 500
            
