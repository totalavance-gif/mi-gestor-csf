from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup  # Necesitas agregar 'beautifulsoup4' a requirements.txt
import urllib3
import ssl

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

        # URL del Validador que no requiere e.firma
        validador_url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        
        session = requests.Session()
        session.mount('https://', SSLAdapter())

        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36'
        }

        response = session.get(validador_url, headers=headers, timeout=20, verify=False)

        if response.status_code == 200:
            # --- LÓGICA DE EXTRACCIÓN (SCRAPING) ---
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscamos las celdas de la tabla de resultados
            # El SAT suele usar IDs o clases específicas en su JSF
            datos = {}
            tablas = soup.find_all('table')
            
            if tablas:
                # Extraemos filas de la tabla de datos generales
                filas = soup.find_all('tr')
                for fila in filas:
                    cols = fila.find_all('td')
                    if len(cols) >= 2:
                        campo = cols[0].get_text(strip=True).replace(':', '')
                        valor = cols[1].get_text(strip=True)
                        datos[campo] = valor

                return jsonify({
                    "status": "success",
                    "data": datos,
                    "source": "SAT Validador Móvil"
                })
            
            return jsonify({"message": "Se accedió al portal pero no se encontraron datos. Verifica RFC/IDCIF."}), 404

        return jsonify({"message": "Error de respuesta del SAT"}), response.status_code

    except Exception as e:
        return jsonify({"message": f"Falla en extracción: {str(e)}"}), 500
