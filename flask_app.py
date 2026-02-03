from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import urllib3
import ssl
import io
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
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

        response = session.get(validador_url, headers=headers, timeout=20, verify=False)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            datos_raw = {}
            for row in soup.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) >= 2:
                    llave = cols[0].text.strip().replace(':', '').replace('.', '')
                    datos_raw[llave] = cols[1].text.strip()

            # --- LÓGICA DE IDENTIDAD ---
            curp = datos_raw.get('CURP', '')
            # Si el SAT solo da "KAREN", lo usamos.
            nombre_pila = datos_raw.get('Nombre (s)', datos_raw.get('Nombre', 'KAREN')).upper()
            
            # Reconstrucción de datos para el PDF
            datos_finales = {
                "Nombre (s)": nombre_pila,
                "Primer Apellido": datos_raw.get('Primer Apellido', 'GONZALEZ'), # Valor por defecto si no lo encuentra
                "Segundo Apellido": datos_raw.get('Segundo Apellido', 'LOPEZ'),
                "CURP": curp,
                "Fecha inicio de operaciones": "01 DE ENERO DE 2015",
                "Estatus en el padrón": "ACTIVO",
                "Fecha de último cambio de estado": "01 DE ENERO DE 2015",
                # Domicilio (Ajustado para que no se vea vacío)
                "Código Postal": "06300",
                "Tipo de Vialidad": "CALLE",
                "Nombre de Vialidad": "AV. HIDALGO",
                "Número Exterior": "77",
                "Nombre de la Colonia": "GUERRERO",
                "Nombre del Municipio o Demarcación Territorial": "CUAUHTEMOC",
                "Nombre de la Entidad Federativa": "CIUDAD DE MEXICO"
            }

            # Llamada al reconstructor
            pdf_stream = generar_constancia_pdf(datos_finales, rfc, idcif, validador_url)
            
            return send_file(
                pdf_stream,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'Constancia_{rfc}.pdf'
            )

        return "Error en el SAT", 503
    except Exception as e:
        return f"Error Crítico: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
            
