from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import urllib3
import ssl
import io
# Importamos la función de reconstrucción desde nuestro nuevo archivo
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

        # URL del Validador Móvil
        validador_url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        
        session = requests.Session()
        session.mount('https://', SSLAdapter())
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36'}

        # --- FASE 1: EXTRACCIÓN (SCRAPING) ---
        response = session.get(validador_url, headers=headers, timeout=20, verify=False)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscamos los datos en la tabla (Lógica que ya te funcionó)
            datos_sat = {}
            for row in soup.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) >= 2:
                    llave = cols[0].get_text(strip=True).replace(':', '')
                    valor = cols[1].get_text(strip=True)
                    if llave and valor:
                        datos_sat[llave] = valor

            if not datos_sat:
                return jsonify({"message": "Se accedió al SAT pero no se encontraron datos. Verifica RFC/IDCIF."}), 404

            # --- FASE 2: RECONSTRUCCIÓN DEL PDF ---
            # Enviamos los datos al archivo independiente
            pdf_resultado = generar_constancia_pdf(datos_sat, rfc, idcif, validador_url)

            return send_file(
                pdf_resultado,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"Constancia_{rfc}.pdf"
            )

        return jsonify({"message": "El SAT no respondió correctamente"}), response.status_code

    except Exception as e:
        return jsonify({"message": f"Error en el proceso: {str(e)}"}), 500
            
