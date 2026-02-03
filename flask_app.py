from flask import Flask, render_template, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import ssl
import urllib3
from reconstructor import generar_constancia_pdf # Tu script de PDF

# Desactiva alertas de seguridad
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# --- PARCHE PARA ERROR DH_KEY_TOO_SMALL ---
class SSLAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        # Bajamos el nivel de seguridad solo para esta conexión (Nivel 1)
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extraer_sat', methods=['POST'])
def extraer():
    try:
        rfc = request.form.get('rfc', '').upper().strip()
        idcif = request.form.get('idcif', '').strip()
        url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        
        session = requests.Session()
        session.mount('https://', SSLAdapter())
        # Realizamos la petición con el parche SSL
        r = session.get(url, timeout=15, verify=False)
        
        soup = BeautifulSoup(r.text, 'html.parser')
        datos = {}
        for row in soup.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 2:
                llave = cols[0].text.strip().replace(':', '')
                datos[llave] = cols[1].text.strip()

        return jsonify({
            "status": "success",
            "curp": datos.get('CURP', ''),
            "nombre": datos.get('Nombre (s)', datos.get('Nombre', '')).upper(),
            "rfc": rfc
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
        
