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
    
    # Creamos un túnel de sesión que se borra al terminar la función
    with requests.Session() as s:
        # Disfraz de alta fidelidad
        s.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })

        try:
            # Primero simulamos una visita a la página principal para 'limpiar' el camino
            s.get("https://sinat.sat.gob.mx/CifDirecto/", timeout=10, verify=False)
            
            # Pedimos el PDF como si acabáramos de dar click en su portal
            pdf_url = f"https://sinat.sat.gob.mx/CifDirecto/Home/Index?rfc={rfc}&idCif={idcif}"
            res = s.get(pdf_url, timeout=20, verify=False)

            if res.status_code == 200 and b'%PDF' in res.content:
                return send_file(
                    io.BytesIO(res.content),
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f"CSF_{rfc}.pdf"
                )
            
            return jsonify({"message": "El SAT bloqueó el rastro. Reintenta."}), 404
        except:
            return jsonify({"message": "Falla de red con el SAT."}), 500
                    
