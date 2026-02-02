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

        # URL Oficial del SAT
        target_url = f"https://sinat.sat.gob.mx/CifDirecto/Home/Index?rfc={rfc}&idCif={idcif}"
        
        # Simulamos un navegador real para evitar bloqueos
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'application/pdf, */*',
            'Accept-Language': 'es-MX,es;q=0.9',
            'Referer': 'https://www.sat.gob.mx/'
        }

        # Intentamos la conexión con un tiempo de espera amplio
        response = requests.get(target_url, headers=headers, timeout=30, verify=False)

        if response.status_code == 200 and b'%PDF' in response.content:
            return send_file(
                io.BytesIO(response.content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"CSF_{rfc}.pdf"
            )
            
        return jsonify({"message": "El SAT no encontró la constancia. Revisa RFC e idCIF."}), 404

    except Exception as e:
        # Si falla el DNS de Render, intentamos vía IP interna como último recurso
        try:
            alt_url = f"https://200.57.3.46/CifDirecto/Home/Index?rfc={rfc}&idCif={idcif}"
            response = requests.get(alt_url, headers={'Host': 'sinat.sat.gob.mx'}, timeout=20, verify=False)
            if b'%PDF' in response.content:
                return send_file(io.BytesIO(response.content), mimetype='application/pdf', download_name=f"CSF_{rfc}.pdf")
        except:
            pass
        return jsonify({"message": "Error de conexión con el SAT. Intenta en 1 minuto."}), 500
        
