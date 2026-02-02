from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import urllib3
import ssl
import io
# Importamos tu nuevo reconstructor
from reconstructor import generar_constancia_pdf 

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

class SSLAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
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

        validador_url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        
        session = requests.Session()
        session.mount('https://', SSLAdapter())
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10)'}

        # PASO 1: EXTRAER (Lo que ya funcionaba)
        response = session.get(validador_url, headers=headers, timeout=20, verify=False)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            datos_sat = {cols[0].text.strip().replace(':', ''): cols[1].text.strip() 
                         for row in soup.find_all('tr') if (cols := row.find_all('td'))}

            if not datos_sat:
                return jsonify({"message": "No se encontraron datos en el SAT"}), 404

            # PASO 2: RECONSTRUIR (Llamamos al archivo aparte)
            pdf_binario = generar_constancia_pdf(datos_sat, rfc, idcif, validador_url)

            return send_file(
                pdf_binario,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"Constancia_{rfc}.pdf"
            )

        return jsonify({"message": "El SAT no respondió"}), 503
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500
        
