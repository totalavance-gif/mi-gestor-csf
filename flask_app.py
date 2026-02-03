From flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import urllib3
import ssl

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

# Bypass de Seguridad SSL para el SAT
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

        # URL del validador móvil (la más estable que encontramos)
        validador_url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        
        session = requests.Session()
        session.mount('https://', SSLAdapter())

        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36'
        }

        # Realizamos el scraping de datos
        response = session.get(validador_url, headers=headers, timeout=20, verify=False)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            datos_extraidos = {}
            
            # Buscamos todas las tablas de datos fiscales en el HTML
            for row in soup.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) >= 2:
                    llave = cols[0].text.strip().replace(':', '')
                    valor = cols[1].text.strip()
                    if llave and valor:
                        datos_extraidos[llave] = valor

            if not datos_extraidos:
                return jsonify({"message": "Se entró al SAT pero la tabla está vacía. Verifica ID CIF."}), 404

            return jsonify({
                "status": "success",
                "data": datos_extraidos
            })

        return jsonify({"message": "El SAT no respondió a la consulta de datos."}), 503

    except Exception as e:
        return jsonify({"message": f"Falla en extracción: {str(e)}"}), 500

Este fue el funcionó a este agrega lo de la reconstrucción del PDF para que visualmente se parezca a una constancia de situación fiscal incluye lo del codigo qr
