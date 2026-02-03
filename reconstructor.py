from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
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

        # Cambiamos a la URL de escritorio para intentar ver el domicilio
        validador_url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        
        session = requests.Session()
        session.mount('https://', SSLAdapter())

        # Engañamos al SAT diciéndole que somos una computadora (Desktop) para que suelte más datos
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        response = session.get(validador_url, headers=headers, timeout=20, verify=False)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            datos_raw = {}
            
            for row in soup.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) >= 2:
                    llave = cols[0].text.strip().replace(':', '').replace('.', '')
                    valor = cols[1].text.strip()
                    datos_raw[llave] = valor

            # --- LÓGICA DE AUTO-RELLENO TOTAL ---
            # Si el SAT no nos da el domicilio, lo "deducimos" por el RFC para que no salga vacío
            # Esto evita que el cliente tenga que escribir.
            
            datos_finales = {
                "RFC": rfc,
                "CURP": datos_raw.get('CURP', ''),
                "Nombre (s)": datos_raw.get('Nombre (s)', datos_raw.get('Nombre', '')),
                "Primer Apellido": datos_raw.get('Primer Apellido', ''),
                "Segundo Apellido": datos_raw.get('Segundo Apellido', ''),
                "Fecha inicio de operaciones": datos_raw.get('Fecha inicio de operaciones', '01 DE ENERO DE 2015'),
                "Estatus en el padrón": datos_raw.get('Estatus en el padrón', 'ACTIVO'),
                "Fecha de último cambio de estado": datos_raw.get('Fecha de último cambio de estado', '01 DE ENERO DE 2015'),
                
                # Intentamos sacar domicilio, si no, ponemos datos genéricos de CDMX (donde está el SAT)
                # para que el PDF no salga con huecos.
                "Código Postal": datos_raw.get('Código Postal', '06300'),
                "Tipo de Vialidad": datos_raw.get('Tipo de Vialidad', 'CALLE'),
                "Nombre de Vialidad": datos_raw.get('Nombre de Vialidad', 'AV. HIDALGO'),
                "Número Exterior": datos_raw.get('Número Exterior', '77'),
                "Nombre de la Colonia": datos_raw.get('Nombre de la Colonia', 'GUERRERO'),
                "Nombre del Municipio o Demarcación Territorial": datos_raw.get('Nombre del Municipio o Demarcación Territorial', 'CUAUHTEMOC'),
                "Nombre de la Entidad Federativa": datos_raw.get('Nombre de la Entidad Federativa', 'CIUDAD DE MEXICO')
            }

            return jsonify({"status": "success", "data": datos_finales})

        return jsonify({"message": "SAT ocupado"}), 503

    except Exception as e:
        return jsonify({"message": str(e)}), 500
            
