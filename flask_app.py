from flask import Flask, render_template, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import ssl
import urllib3
from reconstructor import generar_constancia_pdf

# Desactiva alertas de seguridad innecesarias
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# --- PARCHE PARA EL ERROR SSL DEL SAT ---
class SSLAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        # Baja el nivel de seguridad solo para esta conexión para que el SAT la acepte
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = ctx
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
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        r = session.get(url, headers=headers, timeout=15, verify=False)
        
        soup = BeautifulSoup(r.text, 'html.parser')
        datos = {}
        for row in soup.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 2:
                llave = cols[0].text.strip().replace(':', '')
                datos[llave] = cols[1].text.strip()

        if not datos:
            return jsonify({"status": "error", "message": "No se encontraron datos. Verifica el ID CIF."})

        return jsonify({
            "status": "success",
            "curp": datos.get('CURP', ''),
            "nombre": datos.get('Nombre (s)', datos.get('Nombre', '')).upper(),
            "rfc": rfc
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/generar_pdf', methods=['POST'])
def generar():
    try:
        datos_finales = {
            "Nombre (s)": request.form.get('nombre', '').upper(),
            "Primer Apellido": request.form.get('apellido_p', '').upper(),
            "Segundo Apellido": request.form.get('apellido_m', '').upper(),
            "CURP": request.form.get('curp', '').upper(),
            "RFC": request.form.get('rfc', '').upper()
        }
        rfc = datos_finales["RFC"]
        idcif = request.form.get('idcif')
        url_sat = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        
        pdf_stream = generar_constancia_pdf(datos_finales, rfc, idcif, url_sat)
        return send_file(pdf_stream, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')
    except Exception as e:
        return f"Error: {str(e)}", 500
        
