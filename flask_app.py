from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import requests
import io
import random

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
        
        # URL de descarga directa
        url = f"https://sinat.sat.gob.mx/CifDirecto/Home/Index?rfc={rfc}&idCif={idcif}"
        
        # --- ESTRATEGIA: TÚNEL DE RESIDENCIA ---
        # Estos son "servidores puente" que tienen IPs no bloqueadas por el SAT.
        # Intentaremos usar uno de estos para saltar desde Vercel.
        puentes = [
            "https://api.allorigins.win/raw?url=",
            "https://thingproxy.freeboard.io/fetch/",
            "https://corsproxy.io/?"
        ]
        
        puente_elegido = random.choice(puentes)
        target = f"{puente_elegido}{url}"

        # Simulamos un usuario real de Telmex/Infinitum
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0',
            'X-Forwarded-For': f"187.{random.randint(130,250)}.{random.randint(0,255)}.{random.randint(1,254)}",
            'Referer': 'https://www.sat.gob.mx/'
        }

        # Petición a través del túnel
        response = requests.get(target, headers=headers, timeout=25, verify=False)

        if response.status_code == 200 and b'%PDF' in response.content:
            return send_file(
                io.BytesIO(response.content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"CSF_{rfc}.pdf"
            )
        
        return jsonify({"message": "El muro del SAT es fuerte. Reintenta el salto."}), 403

    except Exception as e:
        return jsonify({"message": "Error de túnel residencial. Reintenta."}), 500
        
