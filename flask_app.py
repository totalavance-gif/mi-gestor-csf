from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import requests
import io
import urllib3
import ssl

# Deshabilitamos advertencias de certificados inseguros
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

# --- PARCHE DE SEGURIDAD PARA DH_KEY_TOO_SMALL ---
# Forzamos a Python a aceptar cifrados antiguos del SAT
class SSLAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1') # Baja el nivel de seguridad para el SAT
        ctx.check_hostname = False
        kwargs['ssl_context'] = ctx
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def generar():
    try:
        rfc = request.form.get('rfc', '').upper().strip()
        idcif = request.form.get('idcif', '').strip()

        # Usamos la lógica del QR que encontraste en sat_scraping
        validador_url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        
        session = requests.Session()
        session.mount('https://', SSLAdapter()) # Aplicamos el parche de seguridad

        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36'
        }

        # Intentamos el bypass a través del validador móvil
        response = session.get(validador_url, headers=headers, timeout=20, verify=False)

        if response.status_code == 200:
            # Si entramos, saltamos al PDF directo
            pdf_url = f"https://sinat.sat.gob.mx/CifDirecto/Home/Index?rfc={rfc}&idCif={idcif}"
            pdf_res = session.get(pdf_url, headers=headers, timeout=20, verify=False)

            if b'%PDF' in pdf_res.content:
                return send_file(
                    io.BytesIO(pdf_res.content),
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f"CSF_{rfc}.pdf"
                )
            
            return jsonify({"message": "Validación exitosa, pero el SAT bloqueó el PDF final."}), 403

        return jsonify({"message": "Datos no reconocidos por el SAT."}), 404

    except Exception as e:
        return jsonify({"message": f"Error SSL parchado: {str(e)}"}), 500
        
