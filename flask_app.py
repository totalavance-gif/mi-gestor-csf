from flask import Flask, request, jsonify, render_template, send_file
import requests
from bs4 import BeautifulSoup
import urllib3
import ssl
from reconstructor import generar_constancia_pdf # Tu script que genera el PDF

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
app = Flask(__name__)

# Configuración SSL para el SAT
class SSLAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extraer_sat', methods=['POST'])
def extraer_sat():
    try:
        rfc = request.form.get('rfc', '').upper().strip()
        idcif = request.form.get('idcif', '').strip()
        url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        
        s = requests.Session()
        s.mount('https://', SSLAdapter())
        r = s.get(url, timeout=15, verify=False)
        
        soup = BeautifulSoup(r.text, 'html.parser')
        datos = {}
        for row in soup.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 2:
                datos[cols[0].text.strip()] = cols[1].text.strip()

        return jsonify({
            "status": "success",
            "curp": datos.get('CURP:', ''),
            "nombre": datos.get('Nombre (s):', '').upper(),
            "rfc": rfc
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/generar_pdf', methods=['POST'])
def generar_pdf():
    # Recibe los datos del formulario manual
    datos_finales = {
        "Nombre (s)": request.form.get('nombre'),
        "Primer Apellido": request.form.get('apellido_p'),
        "Segundo Apellido": request.form.get('apellido_m'),
        "CURP": request.form.get('curp'),
        "RFC": request.form.get('rfc'),
        "Código Postal": "06300", # Puedes hacerlo editable también
        "Nombre de Vialidad": "AV. HIDALGO",
        "Número Exterior": "77"
    }
    rfc = datos_finales["RFC"]
    idcif = request.form.get('idcif')
    url_sat = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
    
    pdf_stream = generar_constancia_pdf(datos_finales, rfc, idcif, url_sat)
    return send_file(pdf_stream, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')
    
