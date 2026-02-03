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

# --- PASO 1: EXTRAER DATOS Y DEVOLVER CURP ---
@app.route('/extraer_sat', methods=['POST'])
def extraer_sat():
    try:
        rfc = request.form.get('rfc', '').upper().strip()
        idcif = request.form.get('idcif', '').strip()

        validador_url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        
        session = requests.Session()
        session.mount('https://', SSLAdapter())
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

        response = session.get(validador_url, headers=headers, timeout=15, verify=False)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            datos_raw = {}
            for row in soup.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) >= 2:
                    llave = cols[0].text.strip().replace(':', '').replace('.', '')
                    datos_raw[llave] = cols[1].text.strip()

            # Enviamos los datos para que el index.html los muestre en los inputs
            return jsonify({
                "status": "success",
                "curp_encontrada": datos_raw.get('CURP', ''),
                "nombre_sat": datos_raw.get('Nombre (s)', datos_raw.get('Nombre', '')).upper(),
                "rfc": rfc,
                "mensaje": "CURP extraída. Cópiala para buscar los apellidos si es necesario."
            })
        
        return jsonify({"status": "error", "message": "El SAT no respondió. Verifica RFC e idCIF."}), 503
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- PASO 2: GENERAR EL PDF FINAL CON LOS DATOS MANUALES ---
@app.route('/generar_pdf', methods=['POST'])
def generar_pdf():
    try:
        # Aquí recibimos lo que el usuario ya validó o escribió
        datos_finales = {
            "Nombre (s)": request.form.get('nombre', '').upper(),
            "Primer Apellido": request.form.get('apellido_p', '').upper(),
            "Segundo Apellido": request.form.get('apellido_m', '').upper(),
            "CURP": request.form.get('curp', '').upper(),
            "RFC": request.form.get('rfc', '').upper(),
            # Domicilio automatizado (con coordenadas corregidas)
            "Código Postal": request.form.get('cp', '06300'),
            "Tipo de Vialidad": "CALLE",
            "Nombre de Vialidad": "AV. HIDALGO",
            "Número Exterior": "77",
            "Nombre de la Colonia": "GUERRERO",
            "Nombre del Municipio o Demarcación Territorial": "CUAUHTEMOC",
            "Nombre de la Entidad Federativa": "CIUDAD DE MEXICO"
        }

        rfc = datos_finales["RFC"]
        idcif = request.form.get('idcif', '')
        url_sat = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"

        # Llamamos al reconstructor (asegúrate de que tenga las coordenadas de domicilio bajadas)
        pdf_stream = generar_constancia_pdf(datos_finales, rfc, idcif, url_sat)
        
        return send_file(
            pdf_stream,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'CSF_{rfc}.pdf'
        )
    except Exception as e:
        return f"Error en generación: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
        
