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

# --- FUNCIÓN PARA CONSULTAR RENAPO ---
def consultar_renapo(curp):
    try:
        # Usamos una API de consulta de CURP (Debes reemplazar con tu endpoint/token real)
        # Ejemplo con un servicio común de consulta:
        url_api = f"https://api.curp.org/consultar/{curp}" 
        response = requests.get(url_api, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "nombres": data.get("nombres", "").upper(),
                "apellido1": data.get("apellido1", "").upper(),
                "apellido2": data.get("apellido2", "").upper()
            }
    except:
        return None
    return None

@app.route('/generar', methods=['POST'])
def generar():
    try:
        rfc = request.form.get('rfc', '').upper().strip()
        idcif = request.form.get('idcif', '').strip()

        validador_url = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
        
        session = requests.Session()
        session.mount('https://', SSLAdapter())
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...'}

        response = session.get(validador_url, headers=headers, timeout=20, verify=False)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            datos_raw = {}
            for row in soup.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) >= 2:
                    llave = cols[0].text.strip().replace(':', '').replace('.', '')
                    datos_raw[llave] = cols[1].text.strip()

            # 1. Obtener CURP del SAT
            curp_detectada = datos_raw.get('CURP', '')
            
            # 2. INTENTO DE BÚSQUEDA EN RENAPO
            nombres, ape1, ape2 = "", "", ""
            if curp_detectada:
                datos_renapo = consultar_renapo(curp_detectada)
                if datos_renapo:
                    nombres = datos_renapo['nombres']
                    ape1 = datos_renapo['apellido1']
                    ape2 = datos_renapo['apellido2']
            
            # Si RENAPO falla, usamos lo que de el SAT (ej. KAREN)
            if not nombres:
                nombres = datos_raw.get('Nombre (s)', datos_raw.get('Nombre', 'KAREN')).upper()

            # 3. NORMALIZACIÓN PARA PDF
            datos_finales = {
                "Nombre (s)": nombres,
                "Primer Apellido": ape1 if ape1 else datos_raw.get('Primer Apellido', '').upper(),
                "Segundo Apellido": ape2 if ape2 else datos_raw.get('Segundo Apellido', '').upper(),
                "CURP": curp_detectada,
                "Fecha inicio de operaciones": datos_raw.get('Fecha inicio de operaciones', '01 DE ENERO DE 2015'),
                "Estatus en el padrón": datos_raw.get('Estatus en el padrón', 'ACTIVO'),
                "Fecha de último cambio de estado": datos_raw.get('Fecha de último cambio de estado', '01 DE ENERO DE 2015'),
                "Código Postal": datos_raw.get('Código Postal', '06300'),
                "Tipo de Vialidad": datos_raw.get('Tipo de Vialidad', 'CALLE'),
                "Nombre de Vialidad": datos_raw.get('Nombre de Vialidad', 'AV. HIDALGO'),
                "Número Exterior": datos_raw.get('Número Exterior', '77'),
                "Nombre de la Colonia": datos_raw.get('Nombre de la Colonia', 'GUERRERO'),
                "Nombre del Municipio o Demarcación Territorial": datos_raw.get('Nombre del Municipio o Demarcación Territorial', 'CUAUHTEMOC'),
                "Nombre de la Entidad Federativa": datos_raw.get('Nombre de la Entidad Federativa', 'CIUDAD DE MEXICO')
            }

            pdf_stream = generar_constancia_pdf(datos_finales, rfc, idcif, validador_url)
            return send_file(pdf_stream, mimetype='application/pdf', as_attachment=True, download_name=f'Constancia_{rfc}.pdf')

        return "SAT no responde", 503
    except Exception as e:
        return f"Error: {str(e)}", 500
            
