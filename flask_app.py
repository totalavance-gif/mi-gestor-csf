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
    
    # URL del SAT
    url = f"https://sinat.sat.gob.mx/CifDirecto/Home/Index?rfc={rfc}&idCif={idcif}"
    
    # OPCIÓN: Enmascarar a través de AllOrigins (Funciona como un escudo de IP)
    # Esto hace que el SAT vea la IP de AllOrigins, no la de Vercel.
    proxy_url = f"https://api.allorigins.win/raw?url={url}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/122.0',
        'Referer': 'https://www.sat.gob.mx/'
    }

    try:
        # Petición a través del "máscara"
        res = requests.get(proxy_url, headers=headers, timeout=30)

        if res.status_code == 200 and b'%PDF' in res.content:
            return send_file(
                io.BytesIO(res.content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"CSF_{rfc}.pdf"
            )
            
        return jsonify({"message": "El SAT bloqueó la IP de la máscara. Reintenta."}), 404
    except:
        return jsonify({"message": "Error de máscara de red."}), 500
        
