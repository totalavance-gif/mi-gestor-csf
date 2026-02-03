from flask import Flask, render_template, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import ssl
import urllib3
from reconstructor import generar_constancia_pdf

# Eliminar ruidos de alertas
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# PARCHE DE SEGURIDAD PARA VERCEL (Permite conectar con el SAT)
class SSLAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def generar():
    try:
        rfc = request.form.get('rfc', '').upper().strip()
        idcif = request.form.get('idcif', '').strip()
        
        # Flujo original: Ir al SAT
        validador_url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        
        session = requests.Session()
        session.mount('https://', SSLAdapter())
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = session.get(validador_url, headers=headers, timeout=20, verify=False)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            datos_extraidos = {}
            for row in soup.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) >= 2:
                    llave = cols[0].text.strip().replace(':', '')
                    valor = cols[1].text.strip()
                    datos_extraidos[llave] = valor

            # Si el scraping fue exitoso, devolvemos los datos como antes
            return jsonify({"status": "success", "data": datos_extraidos, "rfc": rfc, "idcif": idcif})
        
        return jsonify({"status": "error", "message": "El SAT no respondió"}), 503
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Nueva ruta para el PDF (Usando los datos que ya extrajimos)
@app.route('/descargar_pdf', methods=['POST'])
def descargar_pdf():
    # Recibe los datos del formulario final
    datos = request.form.to_dict()
    rfc = datos.get('rfc')
    idcif = datos.get('idcif')
    url_sat = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
    
    pdf_stream = generar_constancia_pdf(datos, rfc, idcif, url_sat)
    return send_file(pdf_stream, mimetype='application/pdf', as_attachment=True, download_name=f"CSF_{rfc}.pdf")
                        
