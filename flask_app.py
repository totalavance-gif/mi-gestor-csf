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
            return jsonify({"message": "Datos incompletos"}), 400

        # URL directa
        url = f"https://sinat.sat.gob.mx/CifDirecto/Home/Index?rfc={rfc}&idCif={idcif}"
        
        # Máscara de IP y Agente de Navegador Humano
        # Cambiamos la IP cada vez que edites esto para 'limpiar' el rastro
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'application/pdf, */*',
            'X-Forwarded-For': '201.141.130.18', # IP de ejemplo mexicana
            'Referer': 'https://www.sat.gob.mx/',
            'Connection': 'close'
        }

        # Petición con tiempo de espera generoso (timeout) para evitar el crash de Vercel
        response = requests.get(url, headers=headers, timeout=25, verify=False)

        if response.status_code == 200 and b'%PDF' in response.content:
            return send_file(
                io.BytesIO(response.content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"CSF_{rfc}.pdf"
            )
            
        return jsonify({"message": "El SAT no respondió a la máscara. Reintenta."}), 404

    except Exception as e:
        # Esto nos dirá exactamente qué falló en los logs de Vercel
        print(f"Error: {str(e)}")
        return jsonify({"message": "Error de comunicación. Intenta de nuevo."}), 500
        
